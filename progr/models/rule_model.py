import psycopg2
from psycopg2.extras import RealDictCursor
from progr.utils_app.logger import LOGGER
from progr.config_app.db_config import DB_CONFIG


class RuleModel:
    """
    Модель для работы с таблицей правил IDS/IPS.
    """

    @staticmethod
    def _get_connection():
        """Создаёт подключение к базе данных PostgreSQL."""
        return psycopg2.connect(**DB_CONFIG)

    @staticmethod
    def get_rules(offset=0, limit=10):
        """
        Возвращает список правил с пагинацией.
        :param offset: смещение
        :param limit: количество записей
        :return: список словарей
        """
        query = """
        SELECT rules_id, rules_action, rules_protocol, rules_ip_s, rules_port_s,
               rules_route, rules_ip_d, rules_port_d, rules_msg, rules_content,
               rules_sid, rules_rev, rules_effpol, rules_effotr
        FROM rules
        ORDER BY rules_id
        OFFSET %s LIMIT %s;
        """
        try:
            with RuleModel._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query, (offset, limit))
                    rules = cur.fetchall()
                    LOGGER.info(f"[RuleModel] Получено {len(rules)} правил (offset={offset}, limit={limit})")
                    return rules
        except Exception as e:
            LOGGER.error(f"[RuleModel] Ошибка получения правил: {e}", exc_info=True)
            raise

    @staticmethod
    def get_rule_by_id(rule_id):
        """
        Возвращает одно правило по ID.
        :param rule_id: ID правила
        :return: словарь с данными правила
        """
        query = "SELECT * FROM rules WHERE rules_id = %s;"
        try:
            with RuleModel._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query, (rule_id,))
                    rule = cur.fetchone()
                    LOGGER.info(f"[RuleModel] Получено правило ID={rule_id}")
                    return rule
        except Exception as e:
            LOGGER.error(f"[RuleModel] Ошибка получения правила ID={rule_id}: {e}", exc_info=True)
            raise

    @staticmethod
    def add_rule(rule_data):
        """
        Добавляет новое правило.
        :param rule_data: словарь с данными (ключи = поля БД)
        :return: ID созданного правила
        """
        query = """
        INSERT INTO rules (
            rules_action, rules_protocol, rules_ip_s, rules_port_s,
            rules_route, rules_ip_d, rules_port_d, rules_msg, rules_content,
            rules_sid, rules_rev, rules_effpol, rules_effotr
        ) VALUES (
            %(rules_action)s, %(rules_protocol)s, %(rules_ip_s)s, %(rules_port_s)s,
            %(rules_route)s, %(rules_ip_d)s, %(rules_port_d)s, %(rules_msg)s, %(rules_content)s,
            %(rules_sid)s, %(rules_rev)s, 0, 0
        ) RETURNING rules_id;
        """
        try:
            with RuleModel._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, rule_data)
                    rule_id = cur.fetchone()[0]
                    conn.commit()
                    LOGGER.info(f"[RuleModel] Новое правило добавлено ID={rule_id}")
                    return rule_id
        except Exception as e:
            LOGGER.error(f"[RuleModel] Ошибка добавления правила: {e}", exc_info=True)
            raise

    @staticmethod
    def update_rule(rule_id, updated_data):
        """
        Обновляет существующее правило.
        :param rule_id: ID правила
        :param updated_data: словарь с данными
        """
        set_clause = ", ".join([f"{key} = %({key})s" for key in updated_data.keys()])
        query = f"UPDATE rules SET {set_clause} WHERE rules_id = %(rules_id)s;"
        updated_data["rules_id"] = rule_id

        try:
            with RuleModel._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, updated_data)
                    conn.commit()
                    LOGGER.info(f"[RuleModel] Правило ID={rule_id} обновлено")
        except Exception as e:
            LOGGER.error(f"[RuleModel] Ошибка обновления правила ID={rule_id}: {e}", exc_info=True)
            raise

    @staticmethod
    def add_vote(rule_id, positive=True):
        """
        Добавляет голос (положительный или отрицательный) для правила.
        :param rule_id: ID правила
        :param positive: True = положительный голос, False = отрицательный
        """
        column = "rules_effpol" if positive else "rules_effotr"
        query = f"UPDATE rules SET {column} = {column} + 1 WHERE rules_id = %s;"
        try:
            with RuleModel._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (rule_id,))
                    conn.commit()
                    LOGGER.info(f"[RuleModel] Голос добавлен для правила ID={rule_id}, positive={positive}")
        except Exception as e:
            
            LOGGER.error(f"[RuleModel] Ошибка добавления голоса для ID={rule_id}: {e}", exc_info=True)
            raise