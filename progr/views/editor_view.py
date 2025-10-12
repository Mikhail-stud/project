from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox
)
from PyQt6.QtCore import QTimer
from progr.controllers.editor_controller import EditorController
from progr.dialogs.create_rule_dialog import CreateRuleDialog
from progr.threads.rules_fetcher_db_thread import RulesFetcherThread
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
        self.limit = 20

        self.layout = QVBoxLayout(self)

        # Кнопки управления 
        controls_layout = QHBoxLayout()
        self.prev_button = QPushButton("Предыдущие")
        self.next_button = QPushButton("Следующие")
        self.commit_button = QPushButton("Сохранить изменения")

        self.prev_button.clicked.connect(self.prev_page)
        self.next_button.clicked.connect(self.next_page)
        self.commit_button.clicked.connect(self.commit_changes)

        controls_layout.addWidget(self.prev_button)
        controls_layout.addWidget(self.next_button)
        controls_layout.addWidget(self.commit_button)

        self.layout.addLayout(controls_layout)

        #  Таблица правил 
        self.table = QTableWidget()
        self.layout.addWidget(self.table)

        # Загружаем первую страницу с задержкой
        QTimer.singleShot(0, self.load_rules_async)

    def load_rules_async(self):
        """Асинхронно запускает загрузку правил через поток, не блокируя UI."""
        try:
            # thread_starter — это метод главного окна, у нас MainWindow.start(thread)
            # Получаем его через self.window() (MainWindow) и передаем ссылку на метод.
            starter = getattr(self.window(), "start", None)   # MainWindow.start(thread)
            if starter is None:
                QMessageBox.critical(self, "Ошибка", "Не найден thread-starter у главного окна Load.")
                return
            thread = RulesFetcherThread(self.controller, offset=self.current_offset, limit=self.limit)
            thread.finished.connect(self._on_rules_loaded)  
            thread.error.connect(lambda msg: self._on_rules_error(msg))
            starter(thread) 

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось запустить загрузку правил: {e}")
            LOGGER.error(f"[EditorView] Старт load_rules_async упал: {e}", exc_info=True)

    def _on_rules_loaded(self, rules: list):
        """
        Загружает правила из БД и отображает их в таблице.
        """
        try:
           
            self.table.clear()
            self.table.setColumnCount(5)  # Название, Оценки, Редактировать, Оценить
            self.table.setHorizontalHeaderLabels([ "Название", "SID", "Оценки", "Редактирование", "Оценить"])
            self.table.setRowCount(len(rules))

            for row_idx, rule in enumerate(rules):
                self.table.setItem(row_idx, 0, QTableWidgetItem(str(rule["rules_msg"])))
                self.table.setItem(row_idx, 1, QTableWidgetItem(str(rule["rules_sid"])))
                self.table.setItem(row_idx, 2, QTableWidgetItem(f"✅  {rule.get('rules_effpol', 0)} / ❌ {rule.get('rules_effotr', 0)}"))

                # Кнопка редактирования
                edit_button = QPushButton("✍️")
                edit_button.clicked.connect(lambda _, rid=rule["rules_id"]: self.edit_rule(rid))
                self.table.setCellWidget(row_idx, 3, edit_button)

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
                self.table.setCellWidget(row_idx, 4, vote_widget)

            self.table.resizeColumnsToContents()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось отобразить правила: {e}")
            LOGGER.error(f"[EditorView] Ошибка отрисовки таблицы: {e}", exc_info=True)

    def _on_rules_error(self, msg: str):
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(self, "Ошибка загрузки правил", msg)

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
            self.controller.rate_rule(rule_id, positive)  
            self.load_rules_async()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", "Не удалось оценить правило")
            LOGGER.error(f"[EditorView] Ошибка оценки правила ID={rule_id}: {e}", exc_info=True)

    def commit_changes(self):
        """
        Сохранение всех накопленных изменений через контроллер.
        Контроллер сам поднимет поток BatchSaverThread и свяжет сигналы.
        """
        try:

            starter = getattr(self.window(), "start", None)
            if starter is None:
                QMessageBox.critical(self, "Ошибка", "Не найден thread-starter у главного окна Commit.")
                return

            # Коллбек при успехе: показать сообщение и перезагрузить таблицу
            def on_ok():
                QMessageBox.information(self, "Успех", "Все изменения сохранены в БД.")
                self.load_rules_async()  # обновим текущую страницу

            # Коллбек ошибки: показать причину
            def on_err(msg: str):
                QMessageBox.critical(self, "Ошибка сохранения", msg)

            # Просим контроллер запустить сохранение асинхронно
            self.controller.commit_all_async(
                thread_starter=starter,
                on_finished=on_ok,
                on_error=on_err,
            )

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось запустить сохранение: {e}")

    def next_page(self):
        """
        Переход на следующую страницу правил.
        """
        self.current_offset += self.limit
        self.load_rules_async()

    def prev_page(self):
        """
        Переход на предыдущую страницу правил.
        """
        if self.current_offset >= self.limit:
            self.current_offset -= self.limit
        else:
            self.current_offset = 0
        self.load_rules_async()