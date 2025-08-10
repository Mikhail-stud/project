
from typing import Iterable, Tuple, Any, Optional
from PyQt6.QtCore import QThread, pyqtSignal
from progr.models.rule_model import RuleModel
from progr.utils_app.logger import LOGGER


class BatchSaverThread(QThread):
    """
    Поток для пакетного сохранения изменённых правил в БД.
    Интерфейс совместим с прежним: finished(), error(str).
    """

    finished = pyqtSignal()          # Сигнал при успешном завершении
    error = pyqtSignal(str)          # Сигнал с текстом ошибки

    def __init__(self, modified_rules: Iterable[Tuple[int, dict]], parent: Optional[object] = None) -> None:
        """
        :param modified_rules: Iterable из кортежей (rule_id, updated_data)
        """
        super().__init__(parent)
        self._modified_rules = list(modified_rules) if modified_rules is not None else []

    def run(self) -> None:
        """
        Сохраняет изменённые правила. Поддерживает кооперативную остановку
        через requestInterruption().
        """
        try:
            if not self._modified_rules:
                LOGGER.info("[BatchSaverThread] Нет данных для сохранения.")
                self.finished.emit()
                return

            LOGGER.info(f"[BatchSaverThread] Сохранение {len(self._modified_rules)} правил...")

            for rule_id, updated_data in self._modified_rules:
                if self.isInterruptionRequested():
                    LOGGER.info("[BatchSaverThread] Прервано по requestInterruption().")
                    return
                LOGGER.debug(f"[BatchSaverThread] Сохранение правила ID={rule_id}: {updated_data}")
                RuleModel.update_rule(rule_id, updated_data)

            LOGGER.info("[BatchSaverThread] Сохранение завершено успешно.")
            self.finished.emit()

        except Exception as e:  # noqa: BLE001
            error_msg = f"Ошибка при сохранении правил: {e}"
            LOGGER.error(f"[BatchSaverThread] {error_msg}", exc_info=True)
            self.error.emit(error_msg)
