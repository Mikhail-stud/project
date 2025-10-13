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
        Возвращает данные для CreateRuleDialog / редактирования.
        """
        try:
            LOGGER.info(f"[EditorController] Получение данных правила ID={rule_id}")
            rule = RuleModel.get_rule_by_id(rule_id)
            if not rule:
                raise ValueError("Правило не найдено")

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
        Копит изменения для пакетного сохранения (через BatchSaverThread).
        Здесь НЕ увеличиваем версию — это обычное обновление по ID.
        """
        is_valid, errors = validate_rule(updated_data)
        if not is_valid:
            LOGGER.warning(f"[EditorController] Ошибка валидации правила ID={rule_id}: {errors}")
            raise ValueError("\n".join(errors))

        try:
            LOGGER.info(f"[EditorController] Изменение правила ID={rule_id}: {updated_data}")
            self._modified_rules.append((rule_id, updated_data))
        except Exception as e:
            LOGGER.error(f"[EditorController] Ошибка при добавлении в очередь на сохранение: {e}", exc_info=True)
            raise

    def commit_all_async(self, thread_starter: callable, on_finished: callable, on_error: callable):
        """
        Запускает пакетное сохранение изменений в БД в отдельном потоке.
        """
        try:
            if not self._modified_rules:
                on_finished()
                return

            rules_batch = list(self._modified_rules)
            self._saver_thread = BatchSaverThread(rules_batch)

            def _done():
                self._modified_rules.clear()
                self._saver_thread = None
                on_finished()

            self._saver_thread.finished.connect(_done)
            self._saver_thread.error.connect(lambda msg: on_error(msg))

            thread_starter(self._saver_thread)

        except Exception as e:
            LOGGER.error(f"[EditorController] Ошибка запуска сохранения: {e}", exc_info=True)
            on_error(str(e))

    def rate_rule(self, rule_id, positive=True):
        LOGGER.info("[EditorController] Запущен для оценки")
        RuleModel.add_vote(rule_id, positive)
