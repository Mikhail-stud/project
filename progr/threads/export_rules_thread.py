from PyQt6.QtCore import QThread, pyqtSignal
from progr.models.export_model import ExportModel
from progr.utils_app.export_rules import export_to_rules_file
from progr.utils_app.logger import LOGGER


class ExportRulesThread(QThread):
    """
    Поток для экспорта правил из БД в файл .rules.
    Работает асинхронно, чтобы не блокировать интерфейс.
    """

    finished = pyqtSignal(str)  # Сообщение об успешной выгрузке
    error = pyqtSignal(str)     # Сообщение об ошибке

    def __init__(self, system_type, file_path):
        """
        :param system_type: тип СЗИ ("IDS" или "IPS")
        :param file_path: путь для сохранения .rules файла
        """
        super().__init__()
        self.system_type = system_type
        self.file_path = file_path

    def run(self):
        try:
            LOGGER.info(f"[ExportRulesThread] Запуск экспорта: system_type={self.system_type}, file={self.file_path}")

            # Получаем правила для выбранного СЗИ
            rules = ExportModel.get_rules_for_system(self.system_type)
            if not rules:
                msg = "Нет правил для экспорта."
                LOGGER.warning(f"[ExportRulesThread] {msg}")
                self.error.emit(msg)
                return

            # Экспортируем в файл с разбиением rules_content
            export_to_rules_file(rules, self.file_path)

            msg = f"Экспортировано {len(rules)} правил в {self.file_path}"
            LOGGER.info(f"[ExportRulesThread] {msg}")
            self.finished.emit(msg)

        except Exception as e:
            error_msg = f"Ошибка экспорта: {e}"
            LOGGER.error(f"[ExportRulesThread] {error_msg}", exc_info=True)
            self.error.emit(error_msg)