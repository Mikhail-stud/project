import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QPushButton)
from main_window import MainWindow





app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
