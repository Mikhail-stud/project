from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFileDialog,
    QComboBox, QMenu, QTableView, QMessageBox, QToolButton, QStyle
)
from PyQt6.QtCore import Qt
#from PyQt6.QtGui import QAction
from progr.controllers.constructor_controller import ConstructorController
from progr.threads.file_loader_thread import FileLoaderThread
from progr.dialogs.create_rule_dialog import CreateRuleDialog
from progr.utils_app.logger import LOGGER
from progr.views.widgets import CheckableHeaderView


class ConstructorView(QWidget):
    """
    Вкладка 'Конструктор':
    - Загрузка логов.
    - Парсинг в таблицу.
    - Создание правил IDS/IPS.
    """

    def __init__(self, thread_manager):
        super().__init__()
        self.thread_manager = thread_manager
        self.controller = ConstructorController()
        self.log_lines = []
        self.df = None
        self.logs_model = None

        self.layout = QVBoxLayout(self)

        #  Кнопка загрузки файла логов 
        self.load_button = QPushButton("Загрузить файл логов")
        self.load_button.clicked.connect(self.load_logs)
        self.layout.addWidget(self.load_button)

        #  Выбор типа парсера 
        self.parser_selector = QComboBox()
        self.parser_selector.addItems(["Apache", "Nginx", "Wordpress", "Bitrix"])
        self.layout.addWidget(self.parser_selector)

        #  Кнопка парсинга 
        self.process_button = QPushButton("Сформировать таблицу логов")
        self.process_button.clicked.connect(self._on_click_parse)
        self.layout.addWidget(self.process_button)
        #self.layout.addStretch()

        # Кнопка с тремя точками (меню)
        self.btn_menu = QToolButton()
        #self.btn_menu.setAutoRaise(True)
        self.btn_menu.setText("⋮")
        #self.btn_menu.setObjectName("columnsMenuButton")
        self.btn_menu.setToolTip("Настройка столбцов")
        self.btn_menu.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        #self.btn_menu.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        #self.btn_menu.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TitleBarMenuButton))
        #self.btn_menu.setFixedSize(28, 24)
        self.columns_menu = QMenu(self)
        self.btn_menu.setMenu(self.columns_menu)
        self.layout.addWidget(self.btn_menu, 0, Qt.AlignmentFlag.AlignRight)

        # Таблица логов 
        self.table = QTableView()
        #self.table.setSortingEnabled(True)
        self.table.setHorizontalHeader(CheckableHeaderView(Qt.Orientation.Horizontal, self.table))
        self.table.setVerticalHeader(CheckableHeaderView(Qt.Orientation.Vertical, self.table))
        self.layout.addWidget(self.table)

        # Кнопка создания правила 
        self.create_rule_button = QPushButton("Создать правило")
        self.create_rule_button.clicked.connect(self._on_click_create_rule)
        self.layout.addWidget(self.create_rule_button)

       

    #  Загрузка файла 
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
            try:
                # Модель создаёт КОНТРОЛЛЕР (с чекбоксами в заголовках)
                self.logs_model = self.controller.create_logs_model(df, parent=self)
                self.table.setModel(self.logs_model)
                self.table.horizontalHeader().viewport().update()
                self.table.verticalHeader().viewport().update()
                self.table.resizeColumnsToContents()
                print("horizontal header type:", type(self.table.horizontalHeader()))
                print("vertical header type:", type(self.table.verticalHeader()))

             # Создаём меню столбцов (показать/скрыть) на основе headers
                self._rebuild_columns_menu()
                self.df = df

            except Exception as e:
                LOGGER.error(f"[ConstructorView] table render error: {e}", exc_info=True)
                QMessageBox.critical(self, "Ошибка", f"Не удалось отобразить таблицу: {e}")
            finally:
                self.process_button.setEnabled(True)

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

    # ---------------- Меню '⋮' — чекбоксы видимости столбцов ----------------
    def _rebuild_columns_menu(self):
        self.columns_menu.clear()
        if not self.logs_model:
            return
        headers = self.logs_model.headers()
        for i, name in enumerate(headers):
            act = self.columns_menu.addAction(name)
            act.setCheckable(True)
            act.setChecked(not self.table.isColumnHidden(i))
            act.toggled.connect(lambda checked, col=i: self.table.setColumnHidden(col, not checked))


        # ПОДСКАЗКА: чтобы добавить новый столбец или переименовать —
        # см. controllers/constructor_controller.py -> create_logs_model(headers)

    # ---------------- Клики по заголовкам для (де)выбора ----------------
    def _on_header_column_clicked(self, section: int):
        if not self.logs_model:
            return
        self.logs_model.toggle_column_checked(section)

    def _on_header_row_clicked(self, section: int):
        if not self.logs_model:
            return
        self.logs_model.toggle_row_checked(section)

    # ---------------- Создать правило с автоподстановкой из выбора ----------------
    def _on_click_create_rule(self):
        if not self.logs_model:
            QMessageBox.warning(self, "Нет данных", "Сначала сформируйте таблицу логов.")
            return

        # Сбор префилла делает контроллер (из отмеченных колонок/строк)
        prefill = self.controller.build_prefill_from_selection(self.logs_model)

        # Открываем диалог создания правила с prefill
        dlg = CreateRuleDialog(self, controller=self.controller, rule_data=prefill)
        if dlg.exec():
            rule_data = dlg.get_data()
            QMessageBox.information(self, "Ок", "Данные для правила приняты (можно передать в БД контроллеру).")

