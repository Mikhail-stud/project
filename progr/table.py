import psycopg2
from psycopg2.extras import DictCursor
from PyQt6.QtWidgets import (QWidget, QLabel, QPushButton, QVBoxLayout, QScrollArea, QHBoxLayout, QMessageBox, QDialog, QLineEdit, QSizePolicy)
from PyQt6.QtGui import QIcon


fields_names = [
    "Действие:", "Протокол:", "IP источника:", "Порт источника:", "Направление:",
    "IP получателя:", "Порт получателя:", "Название правила:", "Содержимое:", "SID:", "Версия:"
]
names_columns = [
    "rules_action", "rules_protocol", "rules_ip_s", "rules_port_s", "rules_route",
    "rules_ip_d", "rules_port_d","rules_msg", "rules_content", "rules_sid", "rules_rev"
]

class RuleEditDialog(QDialog):
    def __init__(self, rule_data: dict = None):
        super().__init__()
        self.setWindowTitle("Редактировать правило")
        self.resize(800, 600)

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


quantity_rec_page = 10

class EditorTab(QWidget):
    def __init__(self,):
        super().__init__()
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.current_page = 0
        self.modified_rules = {}

        #Добавление кнопки Обновить и ее функции
        top_bar = QHBoxLayout()
        self.refresh_button = QPushButton("Обновить")
        self.refresh_button.clicked.connect(self.commit_changes)
        top_bar.addStretch()
        top_bar.addWidget(self.refresh_button)
        self.main_layout.addLayout(top_bar)

        # Прокручиваемая область для записей
        self.records_area = QVBoxLayout()
        self.records_container = QWidget()
        self.records_container.setLayout(self.records_area)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.records_container)
        self.main_layout.addWidget(scroll)

        # Кнопки навигации
        nav_layout = QHBoxLayout()
        self.prev_button = QPushButton("Назад")
        self.next_button = QPushButton("Следующие")
        self.prev_button.clicked.connect(self.load_previous)
        self.next_button.clicked.connect(self.load_next)
        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.next_button)
        self.main_layout.addLayout(nav_layout)

        self.load_records()

    #Загрузка записей из БД
    def load_records(self):
        # Очистить старые виджеты
        while self.records_area.count():
            item = self.records_area.takeAt(0)
            widget = item.widget()

            if widget:
                widget.setParent(None)
                widget.deleteLater()
        
        #Подключение к БД
        offset = self.current_page * quantity_rec_page
        conn = psycopg2.connect(
        host="127.0.0.1",
        user="postgres",
        password="admin",
        port=5432,
        dbname="proga_db"
        )

        cursor = conn.cursor(cursor_factory=DictCursor)
        cursor.execute("SELECT rules_id, rules_action, rules_protocol, rules_ip_s, rules_port_s, rules_route, rules_ip_d, rules_port_d, rules_msg, rules_content, rules_sid, rules_rev, rules_effpol, rules_effotr FROM rules ORDER BY rules_id LIMIT %s OFFSET %s", (quantity_rec_page, offset))
        self.result = cursor.fetchall()
        cursor.close()
        conn.close()

        
        for row in self.result:
            self.records_area.addWidget(self.create_record_widget(row))

    #Создание кнопок рядом с записями
    def create_record_widget(self, record):
        rules_id, rules_action, rules_protocol, rules_ip_s, rules_port_s, rules_route, rules_ip_d, rules_port_d, rules_msg, rules_content, rules_sid, rules_rev, rules_effpol, rules_effotr = record
        widget = QWidget()
        layout = QHBoxLayout()
        widget.setLayout(layout)
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        label = QLabel(f'{rules_action} {rules_protocol} {rules_ip_s} {rules_port_s} {rules_route} {rules_ip_d} {rules_port_d} (msg: "{rules_msg}"; content: "{rules_content}"; sid: {rules_sid}; rev: {rules_rev})')
        label.setWordWrap(True)
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        edit_button = QPushButton("Редактировать")
        edit_button.clicked.connect(lambda: self.open_editor(rules_id))

        green_button = QPushButton()
        green_button.setIcon(QIcon.fromTheme("dialog-apply"))
        green_button.clicked.connect(lambda: self.rate_rule(rules_id, True))
        green_button_count = QLabel(f"{rules_effpol}")
        

        red_button = QPushButton()
        red_button.setIcon(QIcon.fromTheme("dialog-cancel"))
        red_button.clicked.connect(lambda: self.rate_rule(rules_id, False))
        red_button_count = QLabel(f"{rules_effotr}")

        layout.addWidget(label)
        layout.addWidget(edit_button)
        layout.addWidget(green_button)
        layout.addWidget(green_button_count)
        layout.addWidget(red_button)
        layout.addWidget(red_button_count)

        return widget


    def open_editor(self, rule_id):
        conn = psycopg2.connect(
        host="127.0.0.1",
        user="postgres",
        password="admin",
        port=5432,
        dbname="proga_db"
        )

        cursor = conn.cursor()
        cursor.execute(f"SELECT {', '.join(names_columns)} FROM rules WHERE rules_id = %s", (rule_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if row:
            data = dict(zip(names_columns, row))
        else:
            data = {}
        
        dialog = RuleEditDialog()

        if dialog.exec():
            self.modified_rules[rule_id] = dialog.get_data()
            QMessageBox.information(self, "Сохранено", "Изменения сохранены локально")
    #Оценка правил
    def rate_rule(self, rule_id, is_positive: bool):
        conn = psycopg2.connect(
        host="127.0.0.1",
        user="postgres",
        password="admin",
        port=5432,
        dbname="proga_db"
        )

        cursor = conn.cursor()

        if is_positive:
            cursor.execute("UPDATE rules SET rules_effpol = rules_effpol + 1 WHERE rules_id = %s", (rule_id,))
        else:
            cursor.execute("UPDATE rules SET rules_effotr = rules_effotr + 1 WHERE rules_id = %s", (rule_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        QMessageBox.information(self, "Оценка", f"Оценка {'положительная' if is_positive else 'отрицательная'} добавлена.")

    #Сохранение изменений
    def commit_changes(self):

        conn = psycopg2.connect(
        host="127.0.0.1",
        user="postgres",
        password="admin",
        port=5432,
        dbname="proga_db"
        )

        cursor = conn.cursor()

        for rule_id, data in self.modified_rules.items():
            assignments = ", ".join([f"{k} = %s" for k in names_columns])
            values = [data[k] for k in fields_names] + [rule_id]
            cursor.execute(f"UPDATE rules SET {assignments} WHERE rules_id = %s", values)

        conn.commit()
        cursor.close()
        conn.close()
        self.modified_rules.clear()
        self.load_records()
        QMessageBox.information(self, "Успешно", "Все изменения сохранены.")

    #Следующая страница
    def load_next(self):
        self.current_page += 1
        self.load_records()
    #Предыдущая страница
    def load_previous(self):

        if self.current_page > 0:
            self.current_page -= 1
            self.load_records()