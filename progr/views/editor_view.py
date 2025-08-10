from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox
)
from PyQt6.QtCore import Qt
from progr.controllers.editor_controller import EditorController
from progr.dialogs.create_rule_dialog import CreateRuleDialog
from progr.models.rule_model import RuleModel
from progr.utils_app.logger import LOGGER


class EditorView(QWidget):
    """
    Вкладка 'Редактор':
    - Просмотр правил из БД.
    - Редактирование правил.
    - Оценка полезности правил.
    - Пагинация.
    """

    def __init__(self):
        super().__init__()
        self.controller = EditorController()
        self.current_offset = 0
        self.limit = 10

        self.layout = QVBoxLayout(self)

        # === Кнопки управления ===
        controls_layout = QHBoxLayout()
        self.refresh_button = QPushButton("Обновить")
        self.prev_button = QPushButton("Предыдущие")
        self.next_button = QPushButton("Следующие")
        self.commit_button = QPushButton("Сохранить изменения")

        self.refresh_button.clicked.connect(self.load_rules)
        self.prev_button.clicked.connect(self.prev_page)
        self.next_button.clicked.connect(self.next_page)
        self.commit_button.clicked.connect(self.commit_changes)

        controls_layout.addWidget(self.refresh_button)
        controls_layout.addWidget(self.prev_button)
        controls_layout.addWidget(self.next_button)
        controls_layout.addWidget(self.commit_button)

        self.layout.addLayout(controls_layout)

        # === Таблица правил ===
        self.table = QTableWidget()
        self.layout.addWidget(self.table)

        # Загружаем первую страницу
        self.load_rules()

    def load_rules(self):
        """
        Загружает правила из БД и отображает их в таблице.
        """
        try:
            rules = self.controller.get_rules(self.current_offset, self.limit)
            self.table.clear()
            self.table.setColumnCount(4)  # Название, Оценки, Редактировать, Оценить
            self.table.setHorizontalHeaderLabels([ "Название", "Оценки", "Редактирование", "Оценить"])
            self.table.setRowCount(len(rules))

            for row_idx, rule in enumerate(rules):
                self.table.setItem(row_idx, 0, QTableWidgetItem(str(rule["rules_msg"])))
                self.table.setItem(row_idx, 1, QTableWidgetItem(f"✅  {rule.get('rules_effpol', 0)} / ❌ {rule.get('rules_effotr', 0)}"))

                # Кнопка редактирования
                edit_button = QPushButton("✍️")
                edit_button.clicked.connect(lambda _, rid=rule["rules_id"]: self.edit_rule(rid))
                self.table.setCellWidget(row_idx, 2, edit_button)

                # Кнопки оценки
                vote_layout = QHBoxLayout()
                upvote_btn = QPushButton("✅ ")
                downvote_btn = QPushButton("❌")
                upvote_btn.clicked.connect(lambda _, rid=rule["rules_id"]: self.vote_rule(rid, True))
                downvote_btn.clicked.connect(lambda _, rid=rule["rules_id"]: self.vote_rule(rid, False))

                vote_layout.addWidget(upvote_btn)
                vote_layout.addWidget(downvote_btn)
                vote_widget = QWidget()
                vote_widget.setLayout(vote_layout)
                self.table.setCellWidget(row_idx, 3, vote_widget)

            self.table.resizeColumnsToContents()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить правила: {e}")
            LOGGER.error(f"[EditorView] Ошибка загрузки правил: {e}", exc_info=True)

    def edit_rule(self, rule_id):
        """
        Открывает диалог редактирования правила.
        """
        try:
            rule_data = self.controller.get_rule_by_id(rule_id)
            dialog = CreateRuleDialog(self, rule_data=rule_data)
            if dialog.exec():
                updated_data = dialog.get_data()
                self.controller.update_rule(rule_id, updated_data)
                QMessageBox.information(self, "Успех", f"Правило добавлено в очередь на сохранение.")
        except ValueError as ve:
            QMessageBox.warning(self, "Ошибка валидации", str(ve))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", "Не удалось отредактировать правило")
            LOGGER.error(f"[EditorView] Ошибка редактирования правила ID={rule_id}: {e}", exc_info=True)

    def vote_rule(self, rule_id, positive=True):
        """
        Обновляет оценку правила.
        """
        try:
            RuleModel.add_vote(rule_id, positive)  # метод в RuleModel
            self.load_rules()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", "Не удалось оценить правило")
            LOGGER.error(f"[EditorView] Ошибка оценки правила ID={rule_id}: {e}", exc_info=True)

    def commit_changes(self):
        """
        Сохраняет все накопленные изменения в БД.
        """
        try:
            self.controller.commit_all()
            QMessageBox.information(self, "Успех", "Все изменения сохранены в БД.")
            self.load_rules()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить изменения: {e}")
            LOGGER.error(f"[EditorView] Ошибка commit_all: {e}", exc_info=True)

    def next_page(self):
        """
        Переход на следующую страницу правил.
        """
        self.current_offset += self.limit
        self.load_rules()

    def prev_page(self):
        """
        Переход на предыдущую страницу правил.
        """
        if self.current_offset >= self.limit:
            self.current_offset -= self.limit
        else:
            self.current_offset = 0
        self.load_rules()