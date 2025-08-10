
from typing import Optional, List, Any
from PyQt6.QtCore import QThread, pyqtSignal
from progr.models.log_parser import LogParser
from progr.utils_app.logger import LOGGER


class LogParserThread(QThread):
    """
    Поток для парсинга логов в DataFrame без блокировки UI.
    Совместим по интерфейсу: finished(object), error(str).
    """

    finished = pyqtSignal(object)  # pandas.DataFrame
    error = pyqtSignal(str)

    def __init__(self, log_lines: List[str], log_type: str, parent: Optional[object] = None) -> None:
        super().__init__(parent)
        self._log_lines = list(log_lines) if log_lines is not None else []
        self._log_type = str(log_type or "").strip().lower()
        self._parser = LogParser()

    def run(self) -> None:
        try:
            if not self._log_lines:
                LOGGER.warning("[LogParserThread] Пустые данные лога.")
                self.finished.emit(None)  # для совместимости
                return

            if self.isInterruptionRequested():
                LOGGER.info("[LogParserThread] Прервано по requestInterruption() до старта.")
                return

            if self._log_type in ("apache", "nginx", "apache/nginx", "apache_nginx"):
                df = self._parser.parse_apache_nginx(self._log_lines)
            elif self._log_type == "wordpress":
                df = self._parser.parse_wordpress(self._log_lines)
            elif self._log_type == "bitrix":
                df = self._parser.parse_bitrix(self._log_lines)
            else:
                raise ValueError(f"Неизвестный тип логов: {self._log_type}")

            if self.isInterruptionRequested():
                LOGGER.info("[LogParserThread] Прервано по requestInterruption() после парсинга.")
                return

            LOGGER.info(f"[LogParserThread] Парсинг завершён, записей: {len(df) if df is not None else 0}.")
            self.finished.emit(df)
        except Exception as e:  # noqa: BLE001
            error_msg = f"Ошибка парсинга логов ({self._log_type}): {e}"
            LOGGER.error(f"[LogParserThread] {error_msg}", exc_info=True)
            self.error.emit(error_msg)
