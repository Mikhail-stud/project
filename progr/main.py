import sys
from PyQt6.QtWidgets import QApplication
from progr.utils_app.logger import LOGGER
from progr.main_window import MainWindow


def main():
    """Точка входа в приложение."""
    app = QApplication(sys.argv)

    LOGGER.info("=== Запуск Программа Х ===")
    window = MainWindow()
    window.show()

    exit_code = app.exec()
    LOGGER.info("=== Завершение работы приложения ===")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()