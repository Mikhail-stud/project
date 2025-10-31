import psycopg2
from psycopg2.extras import RealDictCursor
from progr.utils_app.logger import LOGGER
from progr.config_app.db_config import DB_CONFIG


class RuleModel:
    """
    Модель для работы с таблицей правил IDS/IPS.
    Ожидаем схему таблицы:
      rules_id (PK, serial/bigserial),
      rules_action, rules_protocol, rules_ip_s, rules_port_s,
      rules_route, rules_ip_d, rules_port_d, rules_msg, rules_content,
      rules_sid (уникальный для UPSERT), rules_rev (int), rules_effpol, rules_effotr
    """

    def _get_connection():
        """Создаёт подключение к базе данных PostgreSQL."""
        return psycopg2.connect(**DB_CONFIG)

    # ---------- ЧТЕНИЕ ----------
    def get_rules(offset=0, limit=10):
        """
        Возвращает список правил с пагинацией.
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

    def get_rule_by_id(rule_id):
        """
        Возвращает одно правило по ID.
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

    def get_rule_by_sid(sid):
        """
        Возвращает одно правило по SID или None.
        """
        query = "SELECT * FROM rules WHERE rules_sid = %s LIMIT 1;"
        try:
            with RuleModel._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query, (sid,))
                    rule = cur.fetchone()
                    LOGGER.info(f"[RuleModel] Получено правило по SID={sid}: {'нашлось' if rule else 'нет'}")
                    return rule
        except Exception as e:
            LOGGER.error(f"[RuleModel] Ошибка получения правила по SID={sid}: {e}", exc_info=True)
            raise

    @staticmethod
    def find_next_free_test_sid(start_sid: int = 7000000, pool_min: int = 7000000, pool_max: int = 7999999) -> int | None:
        """
        Возвращает ближайший свободный SID в тестовом диапазоне (7000000–7999999).
        Если start_sid уже занят — ищет следующее свободное значение выше.
        """
        sql = """
            SELECT gs AS free_sid
            FROM generate_series(%s, %s) AS gs
            LEFT JOIN rules r ON r.rules_sid = gs
            WHERE r.rules_sid IS NULL
            ORDER BY gs
            LIMIT 1;
        """
        with RuleModel._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (max(start_sid, pool_min), pool_max))
                row = cur.fetchone()
                if not row:
                    return None
                # Поддержка и обычного курсора (tuple), и RealDictCursor (dict)
                return row["free_sid"] if isinstance(row, dict) else row[0]

    # ---------- СОЗДАНИЕ / ОБНОВЛЕНИЕ ----------
    def add_rule(rule_data):
        """
        Добавляет новое правило. Ожидает, что rules_rev уже задан (обычно 1).
        Возвращает ID созданного правила.
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

    def update_rule(rule_id, updated_data):
        """
        Обновляет существующее правило по rules_id.
        updated_data — словарь c полями для SET.
        """
        set_clause = ", ".join([f"{key} = %({key})s" for key in updated_data.keys()])
        query = f"UPDATE rules SET {set_clause} WHERE rules_id = %(rules_id)s;"
        query2 = f"UPDATE rules SET rules_rev = rules_rev + 1 WHERE rules_id = %s;"
        updated_data = dict(updated_data)
        updated_data["rules_id"] = rule_id

        try:
            with RuleModel._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, updated_data)
                    cur.execute(query2, (rule_id,))
                    conn.commit()
                    LOGGER.info(f"[RuleModel] Правило ID={rule_id} обновлено")
        except Exception as e:
            LOGGER.error(f"[RuleModel] Ошибка обновления правила ID={rule_id}: {e}", exc_info=True)
            raise

    def update_rule_by_sid(sid, updated_data):
        """
        Обновляет существующее правило по rules_sid.
        updated_data — словарь c полями для SET.
        """
        set_clause = ", ".join([f"{key} = %({key})s" for key in updated_data.keys()])
        query = f"UPDATE rules SET {set_clause} WHERE rules_sid = %(rules_sid)s;"
        updated_data = dict(updated_data)
        updated_data["rules_sid"] = sid

        try:
            with RuleModel._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, updated_data)
                    conn.commit()
                    LOGGER.info(f"[RuleModel] Правило SID={sid} обновлено полями: {list(updated_data.keys())}")
                    return True
        except Exception as e:
            LOGGER.error(f"[RuleModel] Ошибка обновления правила SID={sid}: {e}", exc_info=True)
            raise

    # ---------- ГОЛОСОВАНИЯ ----------
    def add_vote(rule_id, positive=True):
        """
        Добавляет голос (положительный или отрицательный) для правила.
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

   