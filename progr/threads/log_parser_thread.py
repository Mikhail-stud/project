from PyQt6.QtCore import QThread, pyqtSignal
from progr.models.log_parser import LogParser
from progr.utils_app.logger import LOGGER


class LogParserThread(QThread):
    """
    Поток для парсинга логов в DataFrame без блокировки UI.
    """

    finished = pyqtSignal(object)  # Возвращает pandas.DataFrame
    error = pyqtSignal(str)        # Возвращает текст ошибки

    def __init__(self, log_lines, log_type):
        """
        :param log_lines: список строк логов
        :param log_type: тип логов (apache, nginx, wordpress, bitrix)
        """
        super().__init__()
        self.log_lines = log_lines
        self.log_type = log_type
        self.parser = LogParser()

    def run(self):
        """
        Запускает процесс парсинга логов в отдельном потоке.
        """
        try:
            LOGGER.info(f"[LogParserThread] Запуск парсинга: тип={self.log_type}, строк={len(self.log_lines)}")

            if self.log_type in ("apache", "nginx"):
                df = self.parser.parse_apache_nginx(self.log_lines)
            elif self.log_type == "wordpress":
                df = self.parser.parse_wordpress(self.log_lines)
            elif self.log_type == "bitrix":
                df = self.parser.parse_bitrix(self.log_lines)
            else:
                raise ValueError(f"Неизвестный тип логов: {self.log_type}")

            LOGGER.info(f"[LogParserThread] Парсинг завершён, получено {len(df)} записей.")
            self.finished.emit(df)

        except Exception as e:
            error_msg = f"Ошибка парсинга логов ({self.log_type}): {e}"
            LOGGER.error(f"[LogParserThread] {error_msg}", exc_info=True)
            self.error.emit(error_msg)