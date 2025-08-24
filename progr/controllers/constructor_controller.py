from progr.threads.log_parser_thread import LogParserThread
from progr.models.logs_table_model import  LogsTableModel
from progr.models.rule_model import RuleModel
from progr.utils_app.logger import LOGGER
import pandas as pd



class ConstructorController:
    """
    Контроллер вкладки 'Конструктор':
    - Асинхронный парсинг логов (создаёт LogParserThread)
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

            # поток запускает контроллер
            thread_starter(self._parser_thread)

        except Exception as e:
            LOGGER.error(f"[ConstructorController] Не удалось запустить LogParserThread: {e}", exc_info=True)
            on_error(str(e))

    def create_logs_model(self, df: pd.DataFrame, parent=None):
        """
        Создаёт и возвращает модель таблицы логов (LogsTableModel).
        Контроллер нормализует столбцы и формирует rows/headers.

        :param df: pandas.DataFrame с результатом парсинга
        :param parent: родитель для Qt-модели (обычно self из View), чтобы модель не собрал GC
        :return: (model, safe_df)
        """
        if df is None:
            df = pd.DataFrame()

        headers = ["time", "ip", "method", "object", "protocol", "code", "referer", "user_agent"]
        # безопасное выравнивание нужных колонок
        safe_df = df.reindex(columns=headers, fill_value="")

        rows = safe_df.values.tolist()
        model = LogsTableModel(rows, headers, parent=parent)

        LOGGER.info("[ConstructorController] Создана LogsTableModel: rows=%s, cols=%s",
                    len(rows), len(headers))
        return model, safe_df



    def create_rule(self, rule_data):

        LOGGER.info("[ConstructorController] Запуск создания нового правила")
        RuleModel.add_rule(rule_data)

