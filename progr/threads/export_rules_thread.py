
from typing import Optional, List, Dict, Any
from PyQt6.QtCore import QThread, pyqtSignal
from progr.models.export_model import ExportModel
from progr.utils_app.export_rules import export_to_rules_file
from progr.utils_app.logger import LOGGER


class ExportRulesThread(QThread):
    """
    Поток для экспорта правил из БД в файл .rules.
    Работает асинхронно, чтобы не блокировать интерфейс.

    Совместим по интерфейсу: finished(str), error(str).
    """

    finished = pyqtSignal(str)  # Сообщение об успешной выгрузке
    error = pyqtSignal(str)     # Сообщение об ошибке

    def __init__(self, system_type: str, file_path: str, parent: Optional[object] = None) -> None:
        super().__init__(parent)
        self._system_type = str(system_type or "").strip().lower()
        self._file_path = str(file_path)

    def run(self) -> None:
        try:
            LOGGER.info(f"[ExportRulesThread] Экспорт правил: system_type={self._system_type}, file={self._file_path}")

            # NB: не знаем точное имя метода модели в вашем проекте.
            # Используем наиболее очевидный вариант и пробуем несколько.
            rules = ExportModel.get_rules_for_system(self._system_type)
            
            
            if self.isInterruptionRequested():
                LOGGER.info("[ExportRulesThread] Прервано по requestInterruption() до записи файла.")
                return

            if not rules:
                msg = "Нет правил для экспорта."
                LOGGER.warning(f"[ExportRulesThread] {msg}")
                self.error.emit(msg)
                return

            # Экспортируем в файл
            export_to_rules_file(rules, self._file_path)

            msg = f"Экспортировано {len(rules)} правил в {self._file_path}"
            LOGGER.info(f"[ExportRulesThread] {msg}")
            self.finished.emit(msg)

        except Exception as e:  # noqa: BLE001
            error_msg = f"Ошибка экспорта: {e}"
            LOGGER.error(f"[ExportRulesThread] {error_msg}", exc_info=True)
            self.error.emit(error_msg)
