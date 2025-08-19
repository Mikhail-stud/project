from progr.threads.log_parser_thread import LogParserThread
from progr.models.logs_table_model import  LogsTableModel
from progr.utils_app.logger import LOGGER


class ConstructorController:
    """
    Контроллер вкладки 'Конструктор':
    - Асинхронный парсинг логов (создаёт LogParserThread)
    - View НЕ знает о потоках и модели — только отдаёт стартер и коллбеки
    """

    def __init__(self):
        self._parser_thread = None

    def start_log_parse(self, log_lines, log_type, thread_starter, on_finished, on_error):
        """
        Запускает парсинг логов в отдельном потоке.
        :param log_lines: список строк логов
        :param log_type: 'apache' | 'nginx' | 'wordpress' | 'bitrix' (или др.)
        :param thread_starter: функция запуска потоков (обычно MainWindow.start)
        :param on_finished: коллбек pandas.DataFrame -> None
        :param on_error: коллбек str -> None
        """
        try:
            LOGGER.info(f"[ConstructorController] start_log_parse: type={log_type}, lines={len(log_lines)}")
            self._parser_thread = LogParserThread(log_lines, log_type)

            def _done(df):
                LOGGER.info(f"[ConstructorController] Парсинг завершён, записей: {len(df)}")
                self._parser_thread = None
                on_finished(df)

            def _err(msg):
                LOGGER.error(f"[ConstructorController] Ошибка парсинга: {msg}")
                self._parser_thread = None
                on_error(msg)

            self._parser_thread.finished.connect(_done)
            self._parser_thread.error.connect(_err)

            # ВАЖНО: поток запускает ИМЕННО контроллер, а не view
            thread_starter(self._parser_thread)

        except Exception as e:
            LOGGER.error(f"[ConstructorController] Не удалось запустить LogParserThread: {e}", exc_info=True)
            on_error(str(e))

    def table_logs(self, rows, headers):

        LOGGER.info("[ConstructorController] Запуск создания таблицы логов")
        LogsTableModel(rows, headers)
        LOGGER.info("[ConstructorController]  Создание таблицы логов закончено")


