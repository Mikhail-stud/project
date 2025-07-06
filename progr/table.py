import psycopg2
from psycopg2.extras import DictCursor
from PyQt6.QtWidgets import (QWidget, QLabel, QPushButton, QVBoxLayout, QScrollArea, QHBoxLayout, QMessageBox, QDialog, QLineEdit, QSizePolicy)
from PyQt6.QtGui import QIcon



class RuleEditDialog(QDialog):
    def __init__(self, rule_data: dict = None):
        super().__init__()
        self.setWindowTitle("Редактировать правило")
        self.resize(600, 400)

        self.layout = QVBoxLayout()
        self.fields = []
        self.setLayout(self.layout)

        for i in range(11):
            title_edit = QLineEdit()
            value_edit = QLineEdit()

            if rule_data:
                title_edit.setText(rule_data.get(f"title_{i+1}", f"Поле {i+1}"))
                value_edit.setText(rule_data.get(f"value_{i+1}", ""))

            hbox = QHBoxLayout()
            hbox.addWidget(title_edit)
            hbox.addWidget(value_edit)

            self.layout.addLayout(hbox)
            self.fields.append((title_edit, value_edit))

        button_box = QHBoxLayout()
        self.save_button = QPushButton("Сохранить")
        self.cancel_button = QPushButton("Отмена")
        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        button_box.addWidget(self.save_button)
        button_box.addWidget(self.cancel_button)
        self.layout.addLayout(button_box)

    def get_data(self):
        data = {}
        for i, (title_edit, value_edit) in enumerate(self.fields):
            data[f"title_{i+1}"] = title_edit.text()
            data[f"value_{i+1}"] = value_edit.text()
        return data


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


    def load_records(self):
        # Очистить старые виджеты
        while self.records_area.count():
            item = self.records_area.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()

        offset = self.current_page * quantity_rec_page
        conn = psycopg2.connect(
        host="127.0.0.1",
        user="postgres",
        password="admin",
        port=5432,
        dbname="proga_db"
        )

        cursor = conn.cursor(cursor_factory=DictCursor)
        cursor.execute("SELECT rules_id, rules_action, rules_protocol, rules_ip_s, rules_port_s, rules_route, rules_ip_d, rules_port_d, rules_msg, rules_content, rules_sid, rules_rev FROM rules ORDER BY rules_id LIMIT %s OFFSET %s", (quantity_rec_page, offset))
        self.result = cursor.fetchall()
        cursor.close()
        conn.close()

        #for rules in self.result:
        #    print(rules['rules_msg'])
        for row in self.result:
            self.records_area.addWidget(self.create_record_widget(row))


    def create_record_widget(self, record):
        rules_id, rules_action, rules_protocol, rules_ip_s, rules_port_s, rules_route, rules_ip_d, rules_port_d, rules_msg, rules_content, rules_sid, rules_rev = record
        widget = QWidget()
        layout = QHBoxLayout()
        widget.setLayout(layout)
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        label = QLabel(f"[{rules_id}] {rules_action} {rules_protocol} {rules_ip_s} {rules_port_s} {rules_route} {rules_ip_d} {rules_port_d} {rules_msg} {rules_content} {rules_sid} {rules_rev} ")
        label.setWordWrap(True)
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        edit_button = QPushButton("Редактировать")
        edit_button.clicked.connect(lambda: self.open_editor(rules_id))

        green_button = QPushButton()
        green_button.setIcon(QIcon.fromTheme("dialog-apply"))
        green_button.clicked.connect(lambda: self.rate_rule(rules_id, True))

        red_button = QPushButton()
        red_button.setIcon(QIcon.fromTheme("dialog-cancel"))
        red_button.clicked.connect(lambda: self.rate_rule(rules_id, False))

        layout.addWidget(label)
        layout.addWidget(edit_button)
        layout.addWidget(green_button)
        layout.addWidget(red_button)

        return widget


    def open_editor(self, rule_id):
        dialog = RuleEditDialog()
        if dialog.exec():
            data = dialog.get_data()
            self.modified_rules[rule_id] = data
            QMessageBox.information(self, "Сохранено", f"Изменения сохранены локально для ID {rule_id}")


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


    def commit_changes(self):
        if not self.modified_rules:
            QMessageBox.information(self, "Нет изменений", "Нет правил для обновления.")
            return

        conn = psycopg2.connect(
        host="127.0.0.1",
        user="postgres",
        password="admin",
        port=5432,
        dbname="proga_db"
        )
        cursor = conn.cursor()

        for rule_id, data in self.modified_rules.items():
            text_data = "\n".join([f"{data[f'title_{i+1}']}: {data[f'value_{i+1}']}" for i in range(11)])
            cursor.execute("UPDATE rules SET rules_action = %s, rules_protocol = %s, rules_ip_s = %s, rules_port_s = %s, rules_route = %s, rules_ip_d = %s, rules_port_d = %s, rules_msg = %s, rules_content = %s, rules_sid = %s, rules_rev= %s WHERE rules_id = %s", (text_data, rule_id))
        conn.commit()
        cursor.close()
        conn.close()
        self.modified_rules.clear()
        self.load_records()
        QMessageBox.information(self, "Успешно", "Все изменения сохранены.")


    def load_next(self):
        self.current_page += 1
        self.load_records()

    def load_previous(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.load_records()




