from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt
from progr.config_app.ui_config import UI_CONFIG
from progr.utils_app.rule_validator import validate_rule


class CreateRuleDialog(QDialog):
    """
    Универсальный диалог для создания или редактирования правила IDS/IPS.
    Поля отображаются на русском, но при сохранении возвращаются ключи БД.
    """

    def __init__(self, parent=None,  controller=None, rule_data: dict | None = None):
        """
        :param parent: родительский виджет
        :param rule_data: словарь с данными для редактирования (ключи = поля БД)
        """
        super().__init__(parent)
        self.controller = controller
        # Настройки окна
        settings = UI_CONFIG["create_rule_dialog"]
        self.setWindowTitle(settings["title_create"] if rule_data is None else settings["title_edit"])
        self.setMinimumSize(settings["min_width"], settings["min_height"])

        self.layout = QVBoxLayout(self)

        # Соответствие "Отображаемое имя" -> "ключ в БД"
        self.field_map = {
            "Действие": "rules_action",
            "Протокол": "rules_protocol",
            "Адрес источника": "rules_ip_s",
            "Порт источника": "rules_port_s",
            "Направление": "rules_route",
            "Адрес получателя": "rules_ip_d",
            "Порт получателя": "rules_port_d",
            "Название правила": "rules_msg",
            "Содержимое правила": "rules_content",
            "SID": "rules_sid",
            "Версия": "rules_rev"
        }

        # Поля ввода
        self.fields = {}

        # Создаём форму
        for label_text, db_key in self.field_map.items():
            row = QHBoxLayout()
            label = QLabel(label_text)
            label.setFixedWidth(175)
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            input_field = QLineEdit()
            if rule_data and db_key in rule_data:
                input_field.setText(str(rule_data[db_key]))

            row.addWidget(label)
            row.addWidget(input_field)
            self.layout.addLayout(row)
            self.fields[db_key] = input_field

        # Кнопки управления
        buttons_layout = QHBoxLayout()
        save_btn = QPushButton("Создать" if rule_data is None else "Сохранить")
        cancel_btn = QPushButton("Отмена")
        save_btn.clicked.connect(self._on_save_clicked)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)

        self.layout.addLayout(buttons_layout)

    def _on_save_clicked(self):
        """
        Проверка данных перед сохранением.
        Подсвечивает ошибочные поля и показывает список ошибок.
        """
        rule_data = self.get_data()
        is_valid, errors = validate_rule(rule_data)

        # Сбрасываем подсветку
        for field in self.fields.values():
            field.setStyleSheet("")

        if not is_valid:
            # Подсветка неверных полей
            error_keys = self._get_error_keys(errors)
            for key in error_keys:
                if key in self.fields:
                    self.fields[key].setStyleSheet("background-color: #ffcccc;")
            # Показ сообщений
            QMessageBox.warning(
                self,
                "Ошибка валидации",
                "Обнаружены ошибки:\n\n" + "\n".join(errors)
            )
            return

        self.accept()

    def _get_error_keys(self, errors_list):
        """
        Определяет, какие поля вызвали ошибки, на основе текста ошибки.
        """
        mapping = {
            "Действие": "rules_action",
            "Протокол": "rules_protocol",
            "Направление": "rules_route",
            "IP-адрес источника": "rules_ip_s",
            "порт источника": "rules_port_s",
            "IP-адрес получателя": "rules_ip_d",
            "порт получателя": "rules_port_d",
            "Название правила": "rules_msg",
            "Содержимое правила": "rules_content",
            "SID": "rules_sid",
            "версия": "rules_rev"
        }
        matched_keys = []
        for err in errors_list:
            for text, db_key in mapping.items():
                if text.lower() in err.lower():
                    matched_keys.append(db_key)
        return matched_keys

    def get_data(self):
        """
        Возвращает словарь {ключ_БД: значение} из формы.
        """
        return {db_key: widget.text().strip() for db_key, widget in self.fields.items()}
