# Импортируем библиотеки
import psycopg2
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QDialog, QLabel, QComboBox, QTableWidget,
    QLineEdit, QHBoxLayout, QMessageBox, QTableWidgetItem, QFileDialog
)
from PyQt6.QtCore import Qt, QSize
import pandas as pd
import re
    

# Основной класс вкладки конструктора
class ConstructorTab(QWidget):
    def __init__(self):
        super().__init__()

        self.new_rules = {}

        # Главный вертикальный layout для размещения всех элементов интерфейса
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Выбор файла
        file_layout = QHBoxLayout()
        self.file_label = QLabel("Файл не выбран")  # Отображает путь к выбранному файлу
        self.select_button = QPushButton("Выбрать файл")
        self.select_button.clicked.connect(self.select_file) # При нажатии вызывается функция выбора файла
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(self.select_button)
        self.layout.addLayout(file_layout)

        # Выпадающий список выбора типа логов
        parser_layout = QHBoxLayout()
        self.parser_type = QComboBox()
        self.parser_type.addItems(["Apache", "NGINX", "WordPress", "Bitrix"])
        parser_layout.addWidget(QLabel("Тип логов:"))
        parser_layout.addWidget(self.parser_type)
        self.layout.addLayout(parser_layout)

        # Кнопка парсинга логов
        self.parse_button = QPushButton("Сформировать таблицу логов")
        self.parse_button.clicked.connect(self.parse_logs)
        self.layout.addWidget(self.parse_button)

        # Кнопка открытия окна создания правила
        self.create_btn = QPushButton("Создать правило")
        self.create_btn.clicked.connect(self.open_create_dialog)
        self.layout.addWidget(self.create_btn)

        # Подключение к базе данных PostgreSQL
        self.conn = psycopg2.connect(
        host="127.0.0.1",
        user="postgres",
        password="admin",
        port=5432,
        dbname="proga_db"
        )
        self.cur = self.conn.cursor() # Создание курсора для выполнения SQL-запросов
        
        # Таблица для отображения логов
        self.table = QTableWidget()
        self.layout.addWidget(self.table)

        # Переменная для хранения распарсенных данных
        self.log_data = pd.DataFrame()

    def select_file(self):
        # Открывает диалог выбора файла и сохраняет путь
        file_name, _ = QFileDialog.getOpenFileName(self, "Выберите лог-файл", "", "Log files (*.log *.txt)")
        if file_name:
            self.file_label.setText(file_name)
            self.file_path = file_name

    def parse_logs(self):
        # Определяет тип логов и запускает парсинг выбранного файла
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
        
        # Парсит строки логов в зависимости от выбранного формата
        structured = []
        if parser_type in ["Apache", "NGINX"]:
            # Регулярное выражение для логов Apache/NGINX
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
        elif parser_type in ["WordPress", "Bitrix"]:
            # Заглушка для CMS логов — просто сохраняем как строку
            for line in lines:
                structured.append({"CMS лог": line.strip()})
        return pd.DataFrame(structured)
    
    def update_table(self):
        # Отображает DataFrame в виде таблицы на интерфейсе
        df = self.log_data
        self.table.setColumnCount(len(df.columns))
        self.table.setRowCount(len(df.index))
        self.table.setHorizontalHeaderLabels(df.columns)

        for i in range(len(df.index)):
            for j in range(len(df.columns)):
                self.table.setItem(i, j, QTableWidgetItem(str(df.iat[i, j])))

    def open_create_dialog(self):
        # Открывает окно для ввода данных нового правила
        dialog = QDialog(self)
        dialog.setWindowTitle("Создание правила")
        dialog.resize(QSize(800, 600))
        layout = QVBoxLayout(dialog)

        # Заголовки и поля для ввода
        self.inputs = {}
        fields_names = [
            "Действие:", "Протокол:", "IP источника:", "Порт источника:", "Направление:",
            "IP получателя:", "Порт получателя:", "Название правила:", "Содержимое:", "SID:", "Версия:"
        ]
        names_columns = [
            "rules_action", "rules_protocol", "rules_ip_s", "rules_port_s", "rules_route",
            "rules_ip_d", "rules_port_d","rules_msg", "rules_content", "rules_sid", "rules_rev", "rules_effpol", "rules_effotr"
        ]

        for i, label in enumerate(fields_names):
            row = QHBoxLayout()
            row.addWidget(QLabel(label))
            input_field = QLineEdit()
            row.addWidget(input_field)
            layout.addLayout(row)
            self.inputs[names_columns[i]] = input_field
            
        # Кнопки "Создать" и "Отмена"
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
        # Сохраняет новое правило в базу данных и выводит результат пользователю
        values = {key: self.inputs[key].text() for key in self.inputs}
        columns = ", ".join(values.keys())
        placeholders = ", ".join(["%s"] * len(values))
        query = f"INSERT INTO rules ({columns}) VALUES ({placeholders})"
        self.cur.execute(query, list(values.values()))
        self.conn.commit()
        self.cur.close()
        self.conn.close()
        dialog.accept()
        
         # Формируем строку результата
        result_parts = []
        for key, val in values.items():
            if key == "rules_msg":
                result_parts.append(f'(msg: "{val}";')
            elif key == "rules_content":
                result_parts.append(f'content: "{val}";')
            elif key == "rules_sid":
                result_parts.append(f"sid: {val};")
            elif key == "rules_rev":
                result_parts.append(f"rev: {val})")
            else:
                result_parts.append(val)

        result_text = " ".join(result_parts)
        QMessageBox.information(self, "Результат", result_text)
