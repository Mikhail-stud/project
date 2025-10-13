from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QStyle, QToolTip
)
from PyQt6.QtCore import Qt, QPoint
from progr.config_app.ui_config import UI_CONFIG
from progr.utils_app.rule_validator import validate_rule


class CreateRuleDialog(QDialog):
    """
    Универсальный диалог для создания или редактирования правила IDS/IPS.
    Поля отображаются на русском, но при сохранении возвращаются ключи БД.
    Также добавлены всплывающие подсказки-иконки справа от полей ввода.
    """

    # ─────────────────────────────────────────────────────────────
    # TODO: СЛОВАРЬ ПОДСКАЗОК (менять только здесь!)
    #
    # Ключ = ключ поля БД (как в self.field_map)
    # Значение = текст или HTML-подсказка, которая будет показана при клике
    # на иконку "i" справа от поля ввода.
    #
    # Чтобы добавить/изменить подсказку — просто допиши сюда пару "ключ: текст".
    # ─────────────────────────────────────────────────────────────
    HELP_TEXTS = {
        "rules_action": "<b>Действие</b> — например: alert, drop, log, pass, activate, dynamic, reject, sdrop.",
        "rules_protocol": "<b>Протокол</b> — например: TCP, UDP, HTTP, ICMP.",
        "rules_ip_s": "<b>IP источника</b> — одиночный адрес или any.",
        "rules_port_s": "<b>Порт источника</b> — число 1–65535 или any.",
        "rules_route": "<b>Направление</b> — стрелка <code>-></code> или -> <->!",
        "rules_ip_d": "<b>IP получателя</b> — одиночный адрес или any.",
        "rules_port_d": "<b>Порт получателя</b> — число 1–65535 или any.",
        "rules_msg": "<b>Название правила</b> — краткое описание события.",
        "rules_content": "<b>Содержимое</b> — ключевые слова, сигнатуры, фразы для поиска.",
        "rules_sid": "<b>SID</b> — уникальный числовой идентификатор правила (если тестовое правило, то 700...).",
        "rules_rev": "<b>Версия</b> — увеличивается автоматически при изменении правила, иначе равно 1."
    }

    def __init__(self, parent=None, controller=None, rule_data: dict | None = None):
        """
        :param parent: родительский виджет
        :param rule_data: словарь с данными для редактирования (ключи = поля БД)
        """
        super().__init__(parent)
        self.controller = controller
        settings = UI_CONFIG["create_rule_dialog"]
        self.setWindowTitle(settings["title_create"] if rule_data is None else settings["title_edit"])
        self.setMinimumSize(settings["min_width"], settings["min_height"])

        self.layout = QVBoxLayout(self)

        # Отображаемое имя -> ключ БД
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

        self.fields = {}

        # ─────────────────────────────────────────────────────────────
        # Создаём форму
        # ─────────────────────────────────────────────────────────────
        for label_text, db_key in self.field_map.items():
            row = QHBoxLayout()
            label = QLabel(label_text)
            label.setFixedWidth(175)
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            input_field = QLineEdit()
            if rule_data and db_key in rule_data:
                input_field.setText(str(rule_data[db_key]))

            # >>> Добавляем иконку-подсказку справа от поля, если есть текст для неё
            if db_key in self.HELP_TEXTS:
                self._add_help_icon(input_field, self.HELP_TEXTS[db_key])

            row.addWidget(label)
            row.addWidget(input_field)
            self.layout.addLayout(row)
            self.fields[db_key] = input_field

        # ─────────────────────────────────────────────────────────────
        # Кнопки управления
        # ─────────────────────────────────────────────────────────────
        buttons_layout = QHBoxLayout()
        save_btn = QPushButton("Создать" if rule_data is None else "Сохранить")
        cancel_btn = QPushButton("Отмена")
        save_btn.clicked.connect(self._on_save_clicked)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        self.layout.addLayout(buttons_layout)

    # ─────────────────────────────────────────────────────────────
    # ВСПОМОГАТЕЛЬНЫЙ МЕТОД: добавляет иконку "i" в QLineEdit
    # ─────────────────────────────────────────────────────────────
    def _add_help_icon(self, lineedit: QLineEdit, tooltip_text: str):
        """
        Добавляет иконку справа внутри поля.
        По клику — показывает QToolTip с подсказкой.
        """
        icon = lineedit.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation)
        action = lineedit.addAction(icon, QLineEdit.ActionPosition.TrailingPosition)
        action.setToolTip("Показать подсказку")

        def _show_tooltip():
            global_pos = lineedit.mapToGlobal(lineedit.rect().bottomRight() + QPoint(-10, 10))
            QToolTip.showText(global_pos, tooltip_text, lineedit)

        action.triggered.connect(_show_tooltip)

    # ─────────────────────────────────────────────────────────────
    # ДАЛЬШЕ КОД ВАЛИДАЦИИ (без изменений)
    # ─────────────────────────────────────────────────────────────
    def _on_save_clicked(self):
        """
        Проверка данных перед сохранением + попытка создать правило.
        Если SID занят — показываем предупреждение и НЕ закрываем диалог.
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
            QMessageBox.warning(
                self,
                "Ошибка валидации",
                "Обнаружены ошибки:\n\n" + "\n".join(errors)
            )
            return

    # === НОВОЕ: пытаемся создать правило через контроллер ===
        if self.controller is not None:
            ok = self.controller.create_rule(rule_data)
            if not ok:
            # Скорее всего, SID уже существует
                QMessageBox.warning(
                    self,
                    "Невозможно создать правило",
                    "Правило с таким SID уже существует.\n"
                    "Пожалуйста, измените поле SID и повторите попытку."
                )
            # Дополнительно подсветим поле SID
                sid_key = "rules_sid"
                if sid_key in self.fields:
                    self.fields[sid_key].setStyleSheet("background-color: #ffefc6;")
                return

    # Если всё ок — закрываем диалог с accept()
        self.accept()

    def _get_error_keys(self, errors_list):
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
        return {db_key: widget.text().strip() for db_key, widget in self.fields.items()}
