import sys
from PyQt6.QtWidgets import (QMainWindow, QApplication, QWidget, QTabWidget, QVBoxLayout, QLabel)
#from PyQt6.QtGui import QPixmap
from table import EditorTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Program X")
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)



        self.editor_tab = EditorTab()
        self.tabs.addTab(self.editor_tab, "Redactor")
       

    def add_tab(self, widget:QWidget, title:str):
        self.tabs.addTab(widget, title)