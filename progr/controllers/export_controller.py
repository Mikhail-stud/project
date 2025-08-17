from progr.threads.export_rules_thread import ExportRulesThread
from progr.utils_app.logger import LOGGER


class ExportController:
    """
    Контроллер экспорта:
    - Поднимает ExportRulesThread
    - Подписывается на сигналы finished/error
    - Делегирует выгрузку в utils.export_rules.export_to_rules_file (вызывается из потока)
    """

    def __init__(self):
        self._thread = None  # держим ссылку, чтобы поток не собрал GC

    def export_rules_async(
        self,
        system_type,      # "IDS" или "IPS"
        file_path,        # путь до .rules
        thread_starter,   # функция запуска потока (обычно MainWindow.start)
        on_finished,      # коллбек при успехе: lambda msg: ...
        on_error,         # коллбек при ошибке: lambda msg: ...
    ):
        """
        Запускает экспорт правил в отдельном потоке через thread_starter.
        Контроллер сам подписывается на сигналы и отдаёт результат во View через коллбеки.
        """
        try:
            LOGGER.info(f"[ExportController] export_rules_async: type={system_type}, path={file_path}")
            self._thread = ExportRulesThread(system_type, file_path)

            def _finish(msg):
                LOGGER.info(f"[ExportController] Экспорт завершён: {msg}")
                self._thread = None
                try:
                    on_finished(msg)
                except Exception as cb_err:
                    LOGGER.error(f"[ExportController] Ошибка в on_finished: {cb_err}", exc_info=True)

            def _err(msg):
                LOGGER.error(f"[ExportController] Ошибка экспорта: {msg}")
                self._thread = None
                try:
                    on_error(msg)
                except Exception as cb_err:
                    LOGGER.error(f"[ExportController] Ошибка в on_error: {cb_err}", exc_info=True)

            self._thread.finished.connect(_finish)
            self._thread.error.connect(_err)

            # Запускаем поток через стартер (например, MainWindow.start(thread))
            thread_starter(self._thread)

        except Exception as e:
            LOGGER.error(f"[ExportController] Не удалось запустить экспорт: {e}", exc_info=True)
            try:
                on_error(str(e))
            except Exception as cb_err:
                LOGGER.error(f"[ExportController] Ошибка при вызове on_error: {cb_err}", exc_info=True)
