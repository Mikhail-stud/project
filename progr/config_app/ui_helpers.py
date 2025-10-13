from PyQt6.QtWidgets import QPushButton, QComboBox

def  fix_widget_wigths (root_widget, width=250):
    for widget in root_widget.findChildren((QPushButton, QComboBox)):
        widget.setFixedWidth(width)