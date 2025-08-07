from PyQt6.QtWidgets import QMainWindow, QTabWidget, QStatusBar, QMenuBar, QMessageBox
from PyQt6.QtGui import QAction
from config.ui_config import UI_CONFIG
from utils.logger import LOGGER
from views.constructor_view import ConstructorView
from views.editor_view import EditorView
from views.export_view import ExportView


class MainWindow(QMainWindow):
    """
    Главное окно приложения с вкладками:
    - Конструктор
    - Редактор
    - Экспорт
    """

    def __init__(self):
        super().__init__()

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

        self.export_tab = ExportView(thread_manager=self)
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
        view_menu = menubar.addMenu("Вид")

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
        if hasattr(current_widget, "load_rules"):
            logger.info("[MainWindow] Обновление данных во вкладке 'Редактор'")
            current_widget.load_rules()
            self.status_bar.showMessage("Данные обновлены", 3000)
        elif hasattr(current_widget, "process_logs"):
            logger.info("[MainWindow] Обновление данных во вкладке 'Конструктор'")
            current_widget.process_logs()
            self.status_bar.showMessage("Логи обновлены", 3000)
        else:
            self.status_bar.showMessage("Эта вкладка не поддерживает обновление", 3000)

    def show_about(self):
        """Показывает информацию о программе."""
        QMessageBox.information(
            self,
            "О программе",
            "IDS/IPS Rule Manager\nВерсия 1.0\nАвтор: Ваше имя\n© 2025"
        )

    def start(self, thread):
        """
        Запуск потоков из View.
        Потоки автоматически завершаются после выполнения.
        """
        thread.start()