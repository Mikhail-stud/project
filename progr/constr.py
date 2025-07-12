from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFileDialog, QMessageBox,
    QComboBox, QLabel, QTableWidget, QTableWidgetItem, QHBoxLayout, QLineEdit, QDialog
)
import pandas as pd

import psycopg2
from psycopg2.extras import DictCursor


fields_names = [
    "Действие:", "Протокол:", "IP источника:", "Порт источника:", "Направление:",
    "IP получателя:", "Порт получателя:", "Название правила:", "Содержимое:", "SID:", "Версия:"
]

names_columns = [
    "rules_action", "rules_protocol", "rules_ip_s", "rules_port_s", "rules_route",
    "rules_ip_d", "rules_port_d","rules_msg", "rules_content", "rules_sid", "rules_rev", "rules_effpol", "rules_effotr"
]

class RuleConstrDialog(QDialog):
    def __init__(self, rule_data: dict = None):
        super().__init__()
        self.setWindowTitle("Создание правила")
        self.resize(600, 500)

        self.layout = QVBoxLayout()
        self.fields = {}
        self.setLayout(self.layout)

        for field in fields_names:
            hbox = QHBoxLayout()
            label = QLabel(field)
            edit = QLineEdit()

            if rule_data and field in rule_data:
                edit.setText(str(rule_data[field]))

            hbox.addWidget(label)
            hbox.addWidget(edit)
            self.layout.addLayout(hbox)
            self.fields[field] = edit

        #Кнопки
        button_box = QHBoxLayout()
        self.save_button = QPushButton("Сохранить")
        self.cancel_button = QPushButton("Отмена")
        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        button_box.addWidget(self.save_button)
        button_box.addWidget(self.cancel_button)
        self.layout.addLayout(button_box)

    def get_data(self):
        return {field: widget.text() for field, widget in self.fields.items()}
    
    

class ConstructorTab(QWidget):
    def __init__(self):
        super().__init__()

        self.new_rules = {}

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        file_layout = QHBoxLayout()
        self.file_label = QLabel("Файл не выбран")
        self.select_button = QPushButton("Выбрать файл")
        self.select_button.clicked.connect(self.select_file)
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(self.select_button)
        self.layout.addLayout(file_layout)

        parser_layout = QHBoxLayout()
        self.parser_type = QComboBox()
        self.parser_type.addItems(["Apache", "NGINX", "WordPress", "Bitrix"])
        parser_layout.addWidget(QLabel("Тип логов:"))
        parser_layout.addWidget(self.parser_type)
        self.layout.addLayout(parser_layout)

        self.parse_button = QPushButton("Сформировать таблицу логов")
        self.parse_button.clicked.connect(self.parse_logs)
        self.layout.addWidget(self.parse_button)

        self.constr_button = QPushButton("Создать правило")
        self.constr_button.clicked.connect(self.open_editor)
        self.layout.addWidget(self.constr_button)
        
        self.table = QTableWidget()
        self.layout.addWidget(self.table)

        self.log_data = pd.DataFrame()

    def select_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Выберите лог-файл", "", "Log files (*.log *.txt)")
        if file_name:
            self.file_label.setText(file_name)
            self.file_path = file_name

    def parse_logs(self):
        parser = self.parser_type.currentText()
        if not hasattr(self, 'file_path'):
            self.file_label.setText("Файл не выбран!")
            return

        with open(self.file_path, 'r') as f:
            lines = f.readlines()

        self.log_data = self.parse_log_lines(lines, parser)
        self.update_table()

    def parse_log_lines(self, lines, parser_type):
        import re

        structured = []
        if parser_type == "Apache":
            pattern = re.compile(r'(?P<ip>\S+) \S+ \S+ \[(?P<time>[^\]]+)\] "(?P<method>\S+) (?P<path>[^"]+) (?P<protocol>[^"]+)" (?P<code>\d+) (?P<size>\d+|-) "(?P<referer>[^"]*)" "(?P<agent>[^"]*)"')
            for line in lines:
                match = pattern.match(line)
                if match:
                    data = match.groupdict()
                    proto_parts = data["protocol"].split("/")
                    data["proto"], data["proto_version"] = proto_parts if len(proto_parts) == 2 else ("", "")
                    structured.append({
                        "Время": data["time"],
                        "IP-адрес": data["ip"],
                        "Метод": data["method"],
                        "Объект": data["path"],
                        "Протокол": data["proto"],
                        "Версия": data["proto_version"],
                        "Код": data["code"],
                        "Referer": data["referer"],
                        "User-Agent": data["agent"]
                    })
        # Можно добавить парсеры для NGINX, WordPress, Bitrix
        return pd.DataFrame(structured)
    
    def update_table(self):
        df = self.log_data
        self.table.setColumnCount(len(df.columns))
        self.table.setRowCount(len(df.index))
        self.table.setHorizontalHeaderLabels(df.columns)

        for i in range(len(df.index)):
            for j in range(len(df.columns)):
                self.table.setItem(i, j, QTableWidgetItem(str(df.iat[i, j])))

    def open_editor(self):

        dialog = RuleConstrDialog()

        if dialog.exec():
            self.new_rules = dialog.get_data()

    def commit_save(self):

        
        conn = psycopg2.connect(
        host="127.0.0.1",
        user="postgres",
        password="admin",
        port=5432,
        dbname="proga_db"
        )

        cursor = conn.cursor()

        for data in self.new_rules.items():
            assignments = ", ".join([f"{k} = %s" for k in names_columns])
            values = [data[k] for k in fields_names]
            cursor.execute(f"INSERT INTO rules({names_columns}) VALUES ({assignments})")

        conn.commit()
        cursor.close()
        conn.close()
        self.new_rules.clear()
        QMessageBox.information(self, "Успешно", "Правило создано.")

