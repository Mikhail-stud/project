from PyQt6.QtCore import QObject
from progr.models.rule_model import RuleModel
from progr.threads.saver_rules_db_thread import BatchSaverThread
from progr.utils_app.rule_validator import validate_rule
from progr.utils_app.logger import LOGGER


class EditorController:
    """
    Контроллер вкладки 'Редактор':
    - Получение правил (с пагинацией).
    - Получение одного правила по ID.
    - Обновление правил (с валидацией).
    - Пакетное сохранение изменений.
    """

    def __init__(self):
        self._modified_rules = []  # Список кортежей (rule_id, updated_data)

    def get_rules(self, offset=0, limit=10):
        """
        Загружает список правил с пагинацией.
        :param offset: смещение для выборки
        :param limit: количество правил
        :return: список словарей с данными правил
        """
        try:
            LOGGER.info(f"[EditorController] Загрузка правил: offset={offset}, limit={limit}")
            rules = RuleModel.get_rules(offset, limit)
            LOGGER.info(f"[EditorController] Загружено правил: {len(rules) if rules else 0}")
            return rules
        except Exception as e:
            LOGGER.error(f"[EditorController] Ошибка загрузки правил: {e}", exc_info=True)
            raise

    def get_rule_by_id(self, rule_id):
        """
        Получает данные одного правила по ID в формате, готовом для CreateRuleDialog.
        :param rule_id: ID правила
        :return: словарь с данными (ключи = поля БД)
        """
        try:
            LOGGER.info(f"[EditorController] Получение данных правила ID={rule_id}")
            rule = RuleModel.get_rule_by_id(rule_id)
            if not rule:
                raise ValueError(f"Правило не найдено")

            return {
                "rules_action": rule.get("rules_action", ""),
                "rules_protocol": rule.get("rules_protocol", ""),
                "rules_ip_s": rule.get("rules_ip_s", ""),
                "rules_port_s": rule.get("rules_port_s", ""),
                "rules_route": rule.get("rules_route", ""),
                "rules_ip_d": rule.get("rules_ip_d", ""),
                "rules_port_d": rule.get("rules_port_d", ""),
                "rules_msg": rule.get("rules_msg", ""),
                "rules_content": rule.get("rules_content", ""),
                "rules_sid": rule.get("rules_sid", ""),
                "rules_rev": rule.get("rules_rev", "")
            }
        except Exception as e:
            LOGGER.error(f"[EditorController] Ошибка получения правила ID={rule_id}: {e}", exc_info=True)
            raise

    def update_rule(self, rule_id, updated_data):
        """
        Добавляет правило в список на сохранение после валидации.
        :param rule_id: ID правила
        :param updated_data: словарь с изменёнными данными (ключи = поля БД)
        """
        # Валидация данных
        is_valid, errors = validate_rule(updated_data)
        if not is_valid:
            LOGGER.warning(f"[EditorController] Ошибка валидации правила ID={rule_id}: {errors}")
            raise ValueError("\n".join(errors))

        try:
            LOGGER.info(f"[EditorController] Изменение правила ID={rule_id}: {updated_data}")
            self._modified_rules.append((rule_id, updated_data))
        except Exception as e:
            LOGGER.error(f"[EditorController] Ошибка при добавлении правила в очередь на сохранение: {e}", exc_info=True)
            raise

    def commit_all_async(self, thread_starter: callable, on_finished: callable, on_error: callable):
        """
        Запускает пакетное сохранение изменений в БД в отдельном потоке.
        :param thread_starter: функция запуска потоков (например, MainWindow.start)
        :param on_finished: коллбек после успешного сохранения (без аргументов)
        :param on_error: коллбек при ошибке (str -> None)
        """
        try:
            if not self._modified_rules:
                # Нет изменений — считаем «успешно» и просто выходим
                on_finished()
                return

            # Копируем очередь, чтобы не мутировать её во время работы потока
            rules_batch = list(self._modified_rules)

            self._saver_thread = BatchSaverThread(rules_batch)

            # Когда поток завершится — чистим очередь и дергаем on_finished
            def _done():
                self._modified_rules.clear()
                self._saver_thread = None
                on_finished()

            self._saver_thread.finished.connect(_done)
            self._saver_thread.error.connect(lambda msg: on_error(msg))

            # Стартуем поток через переданный стартер (обычно MainWindow.start)
            thread_starter(self._saver_thread)

        except Exception as e:
            from progr.utils_app.logger import LOGGER
            LOGGER.error(f"[EditorController] Ошибка запуска сохранения: {e}", exc_info=True)
            on_error(str(e))

    def rate_rule(self, rule_id, positive=True):
        """
        Обновляет оценку правила.
        """
        LOGGER.info("[EditorViews] Happy")
        RuleModel.add_vote(rule_id, positive)  # метод в RuleModel
            