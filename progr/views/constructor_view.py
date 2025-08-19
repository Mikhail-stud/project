from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFileDialog,
    QComboBox, QLineEdit, QTableView, QMessageBox
)
from PyQt6.QtCore import QSortFilterProxyModel, Qt
from progr.controllers.constructor_controller import ConstructorController
from progr.threads.file_loader_thread import FileLoaderThread
from progr.dialogs.create_rule_dialog import CreateRuleDialog
from progr.utils_app.logger import LOGGER


class ConstructorView(QWidget):
    """
    Вкладка 'Конструктор':
    - Загрузка логов.
    - Парсинг в таблицу.
    - Создание правил IDS/IPS.
    """

    def __init__(self, thread_manager):
        controller = ConstructorController()
        super().__init__()
        self.thread_manager = thread_manager
        self.controller = ConstructorController()
        self.log_lines = []
        self.df = None

        self.layout = QVBoxLayout(self)

        # === Кнопка загрузки файла логов ===
        self.load_button = QPushButton("Загрузить файл логов")
        self.load_button.clicked.connect(self.load_logs)
        self.layout.addWidget(self.load_button)

        # === Выбор типа парсера ===
        self.parser_selector = QComboBox()
        self.parser_selector.addItems(["Apache", "Nginx", "Wordpress", "Bitrix"])
        self.layout.addWidget(self.parser_selector)

        # === Кнопка парсинга ===
        self.process_button = QPushButton("Сформировать таблицу логов")
        self.process_button.clicked.connect(self._on_click_parse)
        self.layout.addWidget(self.process_button)

        # === Поле поиска ===
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Поиск по логам...")
        self.layout.addWidget(self.search_field)

        # === Таблица логов ===
        self.table_view = QTableView()
        self.layout.addWidget(self.table_view)

        # === Кнопка создания правила ===
        self.create_rule_button = QPushButton("Создать правило")
        self.create_rule_button.clicked.connect(self.show_create_rule_dialog)
        self.layout.addWidget(self.create_rule_button)

    # === Загрузка файла ===
    def load_logs(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выбери лог-файл", "", "Log files (*.log *.txt)"
        )
        if file_path:
            LOGGER.info(f"[ConstructorView] Выбран файл: {file_path}")
            thread = FileLoaderThread(file_path)
            thread.finished.connect(self.on_file_loaded)
            thread.error.connect(lambda msg: QMessageBox.critical(self, "Ошибка загрузки файла", msg))
            self.thread_manager.start(thread)

    def on_file_loaded(self, lines):
        self.log_lines = lines
        QMessageBox.information(self, "Файл загружен", "Файл логов успешно загружен.")
        LOGGER.info(f"[ConstructorView] Загружено строк: {len(lines)}")

    # === Парсинг логов ===
    def _on_click_parse(self):
        if not self.log_lines:
            QMessageBox.warning(self, "Нет данных", "Сначала загрузите файл логов.")
            return

        log_type = self.parser_selector.currentText()

        # Берём стартер потоков из MainWindow, переданный в конструктор
        starter = getattr(self.thread_manager, "start", None)
        if starter is None:
            QMessageBox.critical(self, "Ошибка", "Не найден thread-starter у главного окна Parse.")
            return

        self.process_button.setEnabled(False)

        def on_ok(df):
            self.process_button.setEnabled(True)
            self.df = df
            headers = ["time", "ip", "method", "object", "protocol", "code", "referer", "user_agent"]
            rows = df[headers].values.tolist() if (df is not None and not df.empty) else []
            model = self.controller.table_logs(rows, headers)
            proxy_model = QSortFilterProxyModel()
            proxy_model.setSourceModel(model)
            proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

            self.search_field.textChanged.connect(proxy_model.setFilterFixedString)

            self.table_view.setModel(proxy_model)
            self.table_view.setSortingEnabled(True)
            self.table_view.resizeColumnsToContents()
            LOGGER.info(f"[ConstructorView] Таблица логов сформирована: {len(rows)} записей")

        def on_err(msg):
            self.process_button.setEnabled(True)
            QMessageBox.critical(self, "Ошибка парсинга", msg)

        self.controller.start_log_parse(
            log_lines=self.log_lines,
            log_type=log_type,
            thread_starter=starter,
            on_finished=on_ok,
            on_error=on_err,
        )

    # === Создание нового правила ===
    def show_create_rule_dialog(self):
        """
        Открывает диалоговое окно для создания нового правила.
        После подтверждения передаёт данные в контроллер для валидации и сохранения.
        """
        dialog = CreateRuleDialog(self)  # Пустой диалог для создания
        if dialog.exec():
            rule_data = dialog.get_data()
            try:
                rule_id = self.controller.create_rule(rule_data)
                QMessageBox.information(self, "Успех", f"Правило успешно создано (ID: {rule_id})")
                LOGGER.info(f"[ConstructorView] Правило успешно создано (ID: {rule_id})")

            except ValueError as ve:
                QMessageBox.warning(self, "Ошибка валидации", {ve})
                LOGGER.warning(f"[ConstructorView] Ошибка валидации str(ve)")

                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось создать правило: {e}")
                LOGGER.critical(f"[ConstructorView] Не удалось создать правило: {e}")
