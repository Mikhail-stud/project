import sys
from PyQt6.QtWidgets import (QMainWindow, QApplication, QWidget, QTabWidget, QVBoxLayout, QLabel)
from table import EditorTab
from constr import ConstructorTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(1300,900)
        self.setWindowTitle("Программа Х")
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.editor_tab = ConstructorTab()
        self.tabs.addTab(self.editor_tab, "Конструктор правил")

        self.editor_tab = EditorTab()
        self.tabs.addTab(self.editor_tab, "Сохраненные правила")


    def add_tab(self, widget:QWidget, title:str):
        self.tabs.addTab(widget, title)