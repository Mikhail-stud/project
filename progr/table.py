import psycopg2
from psycopg2.extras import DictCursor
#from main_window import MainWindow
from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QPushButton, QVBoxLayout)



conn = psycopg2.connect(
    host="127.0.0.1",
    user="postgres",
    password="admin",
    port=5432,
    dbname="proga_db"
)

if conn:
    print("connect to db")


cursor = conn.cursor(cursor_factory=DictCursor)
cursor.execute("SELECT*FROM rules")
result = cursor.fetchall()
print(result)
for rules in result:
    print(rules['rules_msg'])


class EditorTab(QWidget):
    def __init__(self,):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Redact"))
        self.setLayout(layout)