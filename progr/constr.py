from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFileDialog,
    QComboBox, QLabel, QTableWidget, QTableWidgetItem, QHBoxLayout
)
import pandas as pd


class ConstructorTab(QWidget):
    def __init__(self):
        super().__init__()

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