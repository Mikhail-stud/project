from PyQt6.QtCore import QThread, pyqtSignal
from progr.models.rule_model import RuleModel
from progr.utils_app.logger import LOGGER


class RulesFetcherThread(QThread):
    """
    Поток для загрузки правил из БД с пагинацией.
    """

    finished = pyqtSignal(list)  # Список правил
    error = pyqtSignal(str)      # Сообщение об ошибке

    def __init__(self, offset=0, limit=10):
        """
        :param offset: смещение для выборки
        :param limit: количество правил для выборки
        """
        super().__init__()
        self.offset = offset
        self.limit = limit

    def run(self):
        """
        Загружает список правил из БД.
        """
        try:
            LOGGER.info(f"[RulesFetcherThread] Загрузка правил: offset={self.offset}, limit={self.limit}")
            rules = RuleModel.get_rules(self.offset, self.limit)
            LOGGER.info(f"[RulesFetcherThread] Загружено правил: {len(rules) if rules else 0}")
            self.finished.emit(rules)

        except Exception as e:
            error_msg = f"Ошибка при загрузке правил: {e}"
            LOGGER.error(f"[RulesFetcherThread] {error_msg}", exc_info=True)
            self.error.emit(error_msg)