
from PyQt6.QtCore import QThread, pyqtSignal
from progr.controllers.editor_controller import EditorController
from progr.utils_app.logger import LOGGER


class RulesFetcherThread(QThread):
    """
    Поток для загрузки правил из БД с пагинацией.
    Совместим по интерфейсу: finished(list), error(str).
    """

    finished = pyqtSignal(list)   # Список правил
    error = pyqtSignal(str)       # Сообщение об ошибке

    def __init__(self, controller, offset=0, limit=10):
        super().__init__()
        self.controller = EditorController()
        self.offset = offset
        self.limit = limit

    def run(self):
        try:
            LOGGER.info(f"[RulesFetcherThread] Получение правил через контроллер: offset={self.offset}, limit={self.limit}")
            rules = self.controller.get_rules(self.offset, self.limit)  # <-- ключевая строка
            self.finished.emit(rules or [])
            LOGGER.info("[RulesFetcherThread] Загрузка завершена, поток завершается.")
            # никаких циклов — run() вернулся => поток завершён
        except Exception as e:
            msg = f"Ошибка при загрузке правил: {e}"
            LOGGER.error(f"[RulesFetcherThread] {msg}", exc_info=True)
            self.error.emit(msg)
