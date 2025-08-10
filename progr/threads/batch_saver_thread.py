from PyQt6.QtCore import QThread, pyqtSignal
from progr.models.rule_model import RuleModel
from progr.utils_app.logger import LOGGER


class BatchSaverThread(QThread):
    """
    Поток для пакетного сохранения изменённых правил в БД.
    """

    finished = pyqtSignal()         # Сигнал при успешном завершении
    error = pyqtSignal(str)         # Сигнал с текстом ошибки

    def __init__(self, modified_rules):
        """
        :param modified_rules: список кортежей (rule_id, updated_data)
        """
        super().__init__()
        self.modified_rules = modified_rules

    def run(self):
        """
        Запускает процесс пакетного сохранения правил в БД.
        """
        try:
            if not self.modified_rules:
                LOGGER.info("[BatchSaverThread] Нет изменений для сохранения.")
                self.finished.emit()
                return

            LOGGER.info(f"[BatchSaverThread] Сохранение {len(self.modified_rules)} правил...")

            for rule_id, updated_data in self.modified_rules:
                LOGGER.debug(f"[BatchSaverThread] Сохранение правила ID={rule_id}: {updated_data}")
                RuleModel.update_rule(rule_id, updated_data)

            LOGGER.info("[BatchSaverThread] Сохранение завершено успешно.")
            self.finished.emit()

        except Exception as e:
            error_msg = f"Ошибка при сохранении правил: {e}"
            LOGGER.error(f"[BatchSaverThread] {error_msg}", exc_info=True)
            self.error.emit(error_msg)