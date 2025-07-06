import sys
from PyQt6.QtWidgets import (QMainWindow, QApplication, QWidget, QTabWidget, QVBoxLayout, QLabel)
#from PyQt6.QtGui import QPixmap
from table import EditorTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(1000,800)
        self.setWindowTitle("Программа Х")
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)



        self.editor_tab = EditorTab()
        self.tabs.addTab(self.editor_tab, "Таблицы с редактированием")
       

    def add_tab(self, widget:QWidget, title:str):
        self.tabs.addTab(widget, title)