from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFileDialog,
    QComboBox, QMenu, QTableView, QMessageBox, QToolButton, QStyle, QHBoxLayout
)
from PyQt6.QtCore import Qt
import pandas as pd
from progr.controllers.constructor_controller import ConstructorController
from progr.threads.file_loader_thread import FileLoaderThread
from progr.dialogs.create_rule_dialog import CreateRuleDialog
from progr.utils_app.logger import LOGGER
from progr.config_app.ui_helpers import fix_widget_wigths




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
        self.clear_btn = QPushButton("Очистить таблицу логов")
        self.clear_btn.clicked.connect(self._on_clear_clicked)
        btn_row = QHBoxLayout()
        btn_row.addWidget(self.process_button, 1)
        btn_row.addWidget(self.clear_btn)
        
        self.layout.addLayout(btn_row)

        # Кнопка с тремя точками (меню)
        self.btn_menu = QToolButton()
        self.btn_menu.setText("⋮")
        self.btn_menu.setToolTip("Настройка столбцов")
        self.btn_menu.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.columns_menu = QMenu(self)
        self.btn_menu.setMenu(self.columns_menu)
        self.layout.addWidget(self.btn_menu, 0, Qt.AlignmentFlag.AlignRight)

        # Таблица логов 
        self.table = QTableView()
        self.table.setSortingEnabled(True)
        self.layout.addWidget(self.table)

        # Кнопка создания правила 
        self.create_rule_button = QPushButton("Создать правило")
        self.create_rule_button.clicked.connect(self._on_click_create_rule)
        self.layout.addWidget(self.create_rule_button)

        fix_widget_wigths(self, width=250)

       

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
        # Если уже что-то было — склеиваем старое и новое
                if self.df is not None:
                    try:
                        self.df = pd.concat([self.df, df], ignore_index=True)
                    except Exception:
                # На случай несовпадения столбцов — выравниваем
                        self.df = pd.concat([self.df, df.reindex(columns=self.df.columns)], ignore_index=True)
                else:
                    self.df = df

        # Пересобираем модель по совокупным данным
                self.logs_model = self.controller.create_logs_model(self.df, parent=self)
                self.table.setModel(self.logs_model)
                self.table.horizontalHeader().viewport().update()
                self.table.verticalHeader().viewport().update()
                self.table.resizeColumnsToContents()

        # Обновляем меню столбцов
                self._rebuild_columns_menu()

            except Exception as e:
                LOGGER.error(f"[ConstructorView] Ошибка отображения таблицы: {e}", exc_info=True)
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

            try:
                self.controller.create_rule(rule_data)
                QMessageBox.information(self, "Успех", "Правило успешно создано ")
                LOGGER.info("[ConstructorView] Правило успешно создано")

            except ValueError as ve:
                QMessageBox.warning(self, "Ошибка валидации", {ve})
                LOGGER.warning(f"[ConstructorView] Ошибка валидации str(ve)")

                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось создать правило: {e}")
                LOGGER.critical(f"[ConstructorView] Не удалось создать правило: {e}")



    def _on_clear_clicked(self):
        """
        Полностью очищает таблицу логов и внутреннее состояние.
        """
        model = self.table.model()
        try:
            if model and hasattr(model, "clear"):
                model.clear()
            elif model and hasattr(model, "set_rows"):
                model.set_rows([])
            else:
                self.table.setModel(None)
        # Сбросим внутренние ссылки/данные
            self.logs_model = None
            self.df = None
        # Почистим меню столбцов
            self.columns_menu.clear()
        except Exception as e:
            LOGGER.error(f"[ConstructorView] Ошибка очистки: {e}", exc_info=True)