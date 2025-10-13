from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QComboBox, QFileDialog, QMessageBox
from progr.controllers.export_controller import ExportController
from progr.utils_app.logger import LOGGER
from progr.config_app.ui_helpers import fix_widget_wigths



class ExportView(QWidget):
    """
    Вкладка 'Экспорт':
    - Выбор типа СЗИ (IDS/IPS)
    - Выгрузка правил в .rules файл через контроллер (контроллер создает поток)
    """

    def __init__(self):
        """
        :param thread_manager: объект, через который запускаем потоки (MainWindow.start)
        """
        super().__init__()
        self.controller = ExportController()
        self._setup_ui()

        fix_widget_wigths(self, width=250)

    def _setup_ui(self):
        layout = QVBoxLayout()

        self.system_selector = QComboBox()
        self.system_selector.addItems(["IDS", "IPS"])
        layout.addWidget(self.system_selector)

        self.export_button = QPushButton("Выгрузить правила")
        self.export_button.clicked.connect(self._on_export_clicked)
        layout.addWidget(self.export_button)

        self.setLayout(layout)

    def _on_export_clicked(self):
        """Обработчик кнопки 'Выгрузить правила'."""
        system_type = self.system_selector.currentText()
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить файл", "", "Rules files (*.rules)"
        )
        if not file_path:
            return

        self.export_button.setEnabled(False)
        LOGGER.info(f"[ExportView] Запрошен экспорт: system={system_type}, path={file_path}")

        # Получаем стартер потока из главного окна
        starter = getattr(self.window(), "start", None)
        if starter is None:
            QMessageBox.critical(self, "Ошибка", "Не найден thread-starter у главного окна.")
            self.export_button.setEnabled(True)
            return

        # Коллбеки по завершению/ошибке
        def on_finished(msg: str):
            QMessageBox.information(self, "Успех", msg)
            self.export_button.setEnabled(True)

        def on_error(msg: str):
            QMessageBox.critical(self, "Ошибка", msg)
            self.export_button.setEnabled(True)

        # Контроллер создаёт поток и запускает его через стартер
        self.controller.export_rules_async(
            system_type=system_type,
            file_path=file_path,
            thread_starter=starter,
            on_finished=on_finished,
            on_error=on_error,
        )
        

