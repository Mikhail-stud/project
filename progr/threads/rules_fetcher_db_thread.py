
from typing import Optional
from PyQt6.QtCore import QThread, pyqtSignal
from progr.models.rule_model import RuleModel
from progr.utils_app.logger import LOGGER


class RulesFetcherThread(QThread):
    """
    Поток для загрузки правил из БД с пагинацией.
    Совместим по интерфейсу: finished(list), error(str).
    """

    finished = pyqtSignal(list)   # Список правил
    error = pyqtSignal(str)       # Сообщение об ошибке

    def __init__(self, offset: int = 0, limit: int = 10, parent: Optional[object] = None) -> None:
        super().__init__(parent)
        self._offset = int(offset or 0)
        self._limit = int(limit or 0) or 10

    def run(self) -> None:
        try:
            LOGGER.info(f"[RulesFetcherThread] Загрузка правил: offset={self._offset}, limit={self._limit}")
            rules = RuleModel.get_rules(self._offset, self._limit)
            if self.isInterruptionRequested():
                LOGGER.info("[RulesFetcherThread] Прервано по requestInterruption().")
                return
            LOGGER.info(f"[RulesFetcherThread] Загружено правил: {len(rules) if rules else 0}")
            self.finished.emit(rules or [])
        except Exception as e:  # noqa: BLE001
            error_msg = f"Ошибка при загрузке правил: {e}"
            LOGGER.error(f"[RulesFetcherThread] {error_msg}", exc_info=True)
            self.error.emit(error_msg)
