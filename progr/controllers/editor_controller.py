from progr.models.rule_model import RuleModel
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

    def commit_all(self):
        """
        Сохраняет все накопленные изменения в БД.
        """
        try:
            LOGGER.info(f"[EditorController] Сохранение {len(self._modified_rules)} правил...")
            for rule_id, updated_data in self._modified_rules:
                RuleModel.update_rule(rule_id, updated_data)
            self._modified_rules.clear()
            LOGGER.info("[EditorController] Все изменения успешно сохранены")
        except Exception as e:
            LOGGER.error(f"[EditorController] Ошибка при сохранении изменений: {e}", exc_info=True)
            raise