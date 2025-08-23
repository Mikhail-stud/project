from PyQt6.QtWidgets import QMainWindow, QTabWidget, QStatusBar, QMenuBar, QMessageBox
from PyQt6.QtGui import QAction
from progr.config_app.ui_config import UI_CONFIG
from progr.utils_app.logger import LOGGER
from progr.views.constructor_view import ConstructorView
from progr.views.editor_view import EditorView
from progr.views.export_view import ExportView


class MainWindow(QMainWindow):
    """
    Главное окно приложения с вкладками:
    - Конструктор
    - Редактор
    - Экспорт
    """

    def __init__(self):
        super().__init__()  # порядок важен: сначала инициализируем окно

        # Держим ссылки на активные потоки, чтобы их не уничтожало раньше времени
        self._threads = set()

        # Настройки окна
        cfg = UI_CONFIG["main_window"]
        self.setWindowTitle(cfg["title"])
        self.resize(cfg["width"], cfg["height"])

        # Менеджер вкладок
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Добавляем вкладки
        self.constructor_tab = ConstructorView(thread_manager=self)
        self.tabs.addTab(self.constructor_tab, "Конструктор")

        self.editor_tab = EditorView()
        self.tabs.addTab(self.editor_tab, "Редактор")

        self.export_tab = ExportView()
        self.tabs.addTab(self.export_tab, "Экспорт")

        # Статус-бар
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готово")

        # Меню
        self._create_menu()

    def _create_menu(self):
        """Создание меню приложения."""
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)

        # --- Меню Файл ---
        file_menu = menubar.addMenu("Файл")

        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # --- Меню Вид ---
        view_menu = menubar.addMenu("Обновить")

        reload_action = QAction("Обновить данные", self)
        reload_action.triggered.connect(self.reload_data)
        view_menu.addAction(reload_action)

        # --- Меню Помощь ---
        help_menu = menubar.addMenu("Помощь")

        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def reload_data(self):
        """Перезагружает данные на активной вкладке."""
        current_widget = self.tabs.currentWidget()

        # Для вкладки 'Редактор'
        if hasattr(current_widget, "load_rules_async"):
            LOGGER.info("[MainWindow] Обновление данных во вкладке 'Редактор'")
            current_widget.load_rules_async()
            self.status_bar.showMessage("Данные обновлены", 3000)
            return

        # Для вкладки 'Конструктор'
        if hasattr(current_widget, "_on_click_parse"):
            LOGGER.info("[MainWindow] Обновление данных во вкладке 'Конструктор'")
            current_widget._on_click_parse()
            self.status_bar.showMessage("Логи обновлены", 3000)
            return

        self.status_bar.showMessage("Эта вкладка не поддерживает обновление", 3000)

    def show_about(self):
        """Показывает информацию о программе."""
        QMessageBox.information(
            self,
            "О программе",
            "Программа Х\nВерсия 1.0\nАвтор: Михаил\n© 2025"
        )

    # --- Унифицированный менеджер потоков ---
    def start_thread(self, thread):
        """
        Унифицированный запуск QThread/наследников.
        Держим сильную ссылку на поток и очищаем её по завершении,
        чтобы не получить 'QThread: Destroyed while thread is still running'.
        """
        try:
            thread.setParent(self)  # Qt тоже удержит объект
        except Exception:
            pass

        self._threads.add(thread)

        # Чистим ссылки и отдаём объект Qt на удаление после завершения
        thread.finished.connect(lambda: self._threads.discard(thread))
        thread.finished.connect(thread.deleteLater)

        thread.start()

    # --- Обратная совместимость: старое имя метода ---
    def start(self, thread):
        self.start_thread(thread)

    # Корректное закрытие всех активных потоков
    def closeEvent(self, e):
        try:
            for t in list(self._threads):
                try:
                    if hasattr(t, "abort"):
                        t.abort()
                except Exception:
                    pass

                if t.isRunning():
                    t.requestInterruption()
                    try:
                        t.quit()
                    except Exception:
                        pass
                    t.wait(5000)
        finally:
            super().closeEvent(e)
