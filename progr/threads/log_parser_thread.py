# threads/log_parser_thread.py
from PyQt6.QtCore import QThread, pyqtSignal
from progr.utils_app.logger import LOGGER
from progr.models.log_parser_model import LogParser  
import pandas as pd


class LogParserThread(QThread):
    """
    Поток для парсинга логов.
    На вход получает сырые строки и тип парсера, на выход отдаёт pandas.DataFrame.
    """
    finished = pyqtSignal(object)  # pandas.DataFrame
    error = pyqtSignal(str)

    def __init__(self, log_lines, log_type):
        super().__init__()
        self.log_lines = log_lines
        self.log_type = log_type

    def run(self):
        try:
            LOGGER.info(f"[LogParserThread] Запуск парсинга: type={self.log_type}, lines={len(self.log_lines)}")
            parser = LogParser()

            # Унифицированная точка — если в модели есть общий parse(), используем её.
            # Иначе — ветвим по типу.
            if hasattr(parser, "parse"):
                df = parser.parse(self.log_lines, self.log_type)
            else:
                if self.log_type in ("Apache", "Nginx"):
                    df = parser.parse_apache_nginx(self.log_lines)
                elif self.log_type == "Wordpress":
                    df = parser.parse_wordpress(self.log_lines)
                elif self.log_type == "Bitrix":
                    df = parser.parse_bitrix(self.log_lines)
                else:
                    raise ValueError(f"Неизвестный тип парсера: {self.log_type}")

            if df is None:
                df = pd.DataFrame()

            self.finished.emit(df)
            LOGGER.info("[LogParserThread] Парсинг завершён, поток завершается.")

        except Exception as e:
            msg = f"Ошибка парсинга: {e}"
            LOGGER.error(f"[LogParserThread] {msg}", exc_info=True)
            self.error.emit(msg)
