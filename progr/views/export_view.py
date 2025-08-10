from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QComboBox, QFileDialog, QMessageBox
from progr.threads.export_rules_thread import ExportRulesThread
from progr.utils_app.logger import LOGGER


class ExportView(QWidget):
    """
    Вкладка 'Экспорт':
    - Выбор типа СЗИ (IDS/IPS)
    - Выгрузка правил в .rules файл
    """

    def __init__(self, thread_manager):
        """
        :param thread_manager: объект, через который запускаем потоки (MainWindow.start)
        """
        super().__init__()
        self.thread_manager = thread_manager
        self._setup_ui()

    def _setup_ui(self):
        """Создаёт элементы интерфейса."""
        layout = QVBoxLayout()

        # Выбор СЗИ
        self.system_selector = QComboBox()
        self.system_selector.addItems(["IDS", "IPS"])
        layout.addWidget(self.system_selector)

        # Кнопка экспорта
        self.export_button = QPushButton("Выгрузить правила")
        self.export_button.clicked.connect(self.export_rules)
        layout.addWidget(self.export_button)

        self.setLayout(layout)

    def export_rules(self):
        """Запускает процесс экспорта правил."""
        system_type = self.system_selector.currentText()
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить файл", "", "Rules files (*.rules)")
        if not file_path:
            return

        LOGGER.info(f"[ExportView] Запрошен экспорт правил: system_type={system_type}, file={file_path}")
        self.export_button.setEnabled(False)

        # Запуск потока
        thread = ExportRulesThread(system_type, file_path)
        thread.finished.connect(self._on_export_finished)
        thread.error.connect(self._on_export_error)
        self.thread_manager.start(thread)

    def _on_export_finished(self, msg):
        """Обработчик завершения экспорта."""
        QMessageBox.information(self, "Успех", msg)
        self.export_button.setEnabled(True)

    def _on_export_error(self, msg):
        """Обработчик ошибки экспорта."""
        QMessageBox.critical(self, "Ошибка", msg)
        self.export_button.setEnabled(True)