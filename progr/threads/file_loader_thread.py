from PyQt6.QtCore import QThread, pyqtSignal
from progr.utils_app.logger import LOGGER


class FileLoaderThread(QThread):
    """
    Поток для загрузки файла логов без блокировки UI.
    """

    finished = pyqtSignal(list)  # Сигнал при успешной загрузке (список строк)
    error = pyqtSignal(str)      # Сигнал с текстом ошибки

    def __init__(self, file_path):
        """
        :param file_path: путь к загружаемому файлу логов
        """
        super().__init__()
        self.file_path = file_path

    def run(self):
        """
        Читает файл построчно и отправляет результат через сигнал finished.
        """
        try:
            LOGGER.info(f"[FileLoaderThread] Загрузка файла: {self.file_path}")
            with open(self.file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            LOGGER.info(f"[FileLoaderThread] Файл успешно загружен, строк: {len(lines)}")
            self.finished.emit(lines)

        except FileNotFoundError:
            error_msg = f"Файл не найден: {self.file_path}"
            LOGGER.error(f"[FileLoaderThread] {error_msg}")
            self.error.emit(error_msg)

        except Exception as e:
            error_msg = f"Ошибка при чтении файла {self.file_path}: {e}"
            LOGGER.error(f"[FileLoaderThread] {error_msg}", exc_info=True)
            self.error.emit(error_msg)