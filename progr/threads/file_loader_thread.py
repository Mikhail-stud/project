
from typing import Optional, List
from PyQt6.QtCore import QThread, pyqtSignal
from progr.utils_app.logger import LOGGER


class FileLoaderThread(QThread):
    """
    Поток для загрузки файла логов без блокировки UI.
    Совместим по интерфейсу: finished(list[str]), error(str).
    """

    finished = pyqtSignal(list)  # Сигнал при успешной загрузке (список строк)
    error = pyqtSignal(str)      # Сигнал с текстом ошибки

    def __init__(self, file_path: str, parent: Optional[object] = None) -> None:
        super().__init__(parent)
        self._file_path = str(file_path)

    def run(self) -> None:
        try:
            LOGGER.info(f"[FileLoaderThread] Загрузка файла: {self._file_path}")
            lines: List[str] = []
            # Читаем построчно с проверкой прерывания, чтобы не подвесить закрытие
            with open(self._file_path, "r", encoding="utf-8", errors="ignore") as f:
                for i, line in enumerate(f):
                    if self.isInterruptionRequested():
                        LOGGER.info("[FileLoaderThread] Прервано по requestInterruption().")
                        return
                    lines.append(line)
                    # Небольшая батч-буферизация, чтобы не раздувать память на очень больших файлах
                    # (оставлено простым; при необходимости можно делать emit частями)

            LOGGER.info(f"[FileLoaderThread] Файл успешно загружен, строк: {len(lines)}")
            self.finished.emit(lines)

        except FileNotFoundError:
            error_msg = f"Файл не найден: {self._file_path}"
            LOGGER.error(f"[FileLoaderThread] {error_msg}")
            self.error.emit(error_msg)
        except Exception as e:  # noqa: BLE001
            error_msg = f"Ошибка при чтении файла {self._file_path}: {e}"
            LOGGER.error(f"[FileLoaderThread] {error_msg}", exc_info=True)
            self.error.emit(error_msg)
