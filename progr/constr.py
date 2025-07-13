import psycopg2
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QDialog, QLabel, QComboBox, QTableWidget,
    QLineEdit, QHBoxLayout, QMessageBox, QTableWidgetItem, QFileDialog
)
from PyQt6.QtCore import Qt
import pandas as pd

    

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

        self.create_btn = QPushButton("Создать правило")
        self.create_btn.clicked.connect(self.open_create_dialog)
        self.layout.addWidget(self.create_btn)

        self.conn = psycopg2.connect(
        host="127.0.0.1",
        user="postgres",
        password="admin",
        port=5432,
        dbname="proga_db"
        )
        self.cur = self.conn.cursor()
        
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

    def open_create_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Создание правила")
        layout = QVBoxLayout(dialog)

        self.inputs = {}
        fields_names = [
            "Действие:", "Протокол:", "IP источника:", "Порт источника:", "Направление:",
            "IP получателя:", "Порт получателя:", "Название правила:", "Содержимое:", "SID:", "Версия:"
        ]
        names_columns = [
            "rules_action", "rules_protocol", "rules_ip_s", "rules_port_s", "rules_route",
            "rules_ip_d", "rules_port_d","rules_msg", "rules_content", "rules_sid", "rules_rev", "rules_effpol", "rules_effotr"
        ]

        i = 0
        for label in fields_names:
            row_layout = QHBoxLayout()
            lbl = QLabel(label)
            input_field = QLineEdit()
            row_layout.addWidget(lbl)
            row_layout.addWidget(input_field)
            layout.addLayout(row_layout)
            val = names_columns[i]
            self.inputs[val] = input_field
            i += 1
            

        btn_layout = QHBoxLayout()
        create_btn = QPushButton("Создать")
        cancel_btn = QPushButton("Отмена")
        create_btn.clicked.connect(lambda: self.save_rule(dialog))
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(create_btn)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)
        dialog.setLayout(layout)
        dialog.exec()

    def save_rule(self, dialog):
        fields = self.inputs
        values = {key: fields[key].text() for key in fields}

        # Сохраняем в БД
        columns = ", ".join(values.keys())
        placeholders = ", ".join(["%s"] * len(values))
        query = f"INSERT INTO rules ({columns}) VALUES ({placeholders})"
        self.cur.execute(query, list(values.values()))
        self.conn.commit()
        self.cur.close()
        self.conn.close()

        dialog.accept()

    # Формируем строку для отображения
        result_lines = []
        for key, val in values.items():
            if key == "rules_route":
                direction = "->" if val.lower() == "in" else "->" 
                result_lines.append(f"{key}: {direction}")
            else:
                result_lines.append(f"{key}: {val}")
        result_text = " ".join(result_lines)

        QMessageBox.information(self, "Результат", result_text)
