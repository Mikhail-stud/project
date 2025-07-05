import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QPushButton)
#from PyQt6.QtGui import QPixmap
from main_window import MainWindow





app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
