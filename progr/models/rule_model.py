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
        updated_data = dict(updated_data)
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

    # ---------- ОСНОВНАЯ ЛОГИКА ВЕРСИОНИРОВАНИЯ ПО SID ----------
    def add_or_bump_rule(rule_data: dict):
        """
        Если правила с таким SID нет — создаём с rules_rev = 1.
        Если есть — увеличиваем rules_rev на 1.

        Реализация:
          1) Пытаемся сделать UPSERT (ON CONFLICT (rules_sid) DO UPDATE ...).
             НУЖЕН уникальный индекс/ограничение по rules_sid:
               CREATE UNIQUE INDEX IF NOT EXISTS ux_rules_sid ON rules (rules_sid);
             Если его нет, будет исключение — перейдём к п.2 (fallback).
          2) Fallback: SELECT ... FOR UPDATE -> UPDATE (rev+1) ИЛИ INSERT (rev=1).
        Возвращает dict c keys: rules_id, rules_rev, existed (bool).
        """
        if not rule_data or "rules_sid" not in rule_data:
            raise ValueError("rule_data должен содержать ключ 'rules_sid'")

        sid = rule_data["rules_sid"]
        # гарантируем, что при вставке rev=1 (если не передан)
        data_to_insert = dict(rule_data)
        data_to_insert.setdefault("rules_rev", 1)

        # ПОЛНЫЙ список столбцов для INSERT/UPSERT
        insert_cols = (
            "rules_action, rules_protocol, rules_ip_s, rules_port_s, "
            "rules_route, rules_ip_d, rules_port_d, rules_msg, rules_content, "
            "rules_sid, rules_rev, rules_effpol, rules_effotr"
        )

        upsert_sql = f"""
        INSERT INTO rules ({insert_cols})
        VALUES (
            %(rules_action)s, %(rules_protocol)s, %(rules_ip_s)s, %(rules_port_s)s,
            %(rules_route)s, %(rules_ip_d)s, %(rules_port_d)s, %(rules_msg)s, %(rules_content)s,
            %(rules_sid)s, 1, 0, 0
        )
        ON CONFLICT (rules_sid) DO UPDATE
           SET rules_rev = rules.rules_rev + 1
        RETURNING rules_id, rules_rev;
        """

        try:
            with RuleModel._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    try:
                        # Путь 1: UPSERT (требуется уникальный индекс rules_sid)
                        cur.execute(upsert_sql, data_to_insert)
                        row = cur.fetchone()
                        conn.commit()
                        existed = (row["rules_rev"] > 1)
                        LOGGER.info(f"[RuleModel] UPSERT по SID={sid}: rules_id={row['rules_id']}, rev={row['rules_rev']}, existed={existed}")
                        return {"rules_id": row["rules_id"], "rules_rev": row["rules_rev"], "existed": existed}
                    except Exception as upsert_err:
                        # Если нет unique по rules_sid — идём fallback-путём
                        LOGGER.warning(f"[RuleModel] UPSERT не выполнен (возможно, нет уникального индекса по rules_sid). "
                                       f"Перехожу к fallback. Причина: {upsert_err}")
                        conn.rollback()

                    # Путь 2 (fallback): транзакционно блокируем строку по SID
                    cur.execute("BEGIN;")
                    cur.execute("SELECT rules_id, rules_rev FROM rules WHERE rules_sid = %s FOR UPDATE;", (sid,))
                    row = cur.fetchone()

                    if row:
                        new_rev = int(row["rules_rev"] or 0) + 1
                        cur.execute("UPDATE rules SET rules_rev = %s WHERE rules_id = %s RETURNING rules_rev;",
                                    (new_rev, row["rules_id"]))
                        upd = cur.fetchone()
                        cur.execute("COMMIT;")
                        LOGGER.info(f"[RuleModel] REV++ по SID={sid}: rules_id={row['rules_id']}, rev={upd['rules_rev']}")
                        return {"rules_id": row["rules_id"], "rules_rev": upd["rules_rev"], "existed": True}
                    else:
                        # вставляем новую запись с rev=1
                        insert_sql = f"""
                        INSERT INTO rules ({insert_cols})
                        VALUES (
                            %(rules_action)s, %(rules_protocol)s, %(rules_ip_s)s, %(rules_port_s)s,
                            %(rules_route)s, %(rules_ip_d)s, %(rules_port_d)s, %(rules_msg)s, %(rules_content)s,
                            %(rules_sid)s, 1, 0, 0
                        )
                        RETURNING rules_id, rules_rev;
                        """
                        cur.execute(insert_sql, data_to_insert)
                        ins = cur.fetchone()
                        cur.execute("COMMIT;")
                        LOGGER.info(f"[RuleModel] Вставлено новое правило по SID={sid}: rules_id={ins['rules_id']}, rev={ins['rules_rev']}")
                        return {"rules_id": ins["rules_id"], "rules_rev": ins["rules_rev"], "existed": False}
        except Exception as e:
            LOGGER.error(f"[RuleModel] Ошибка add_or_bump_rule SID={sid}: {e}", exc_info=True)
            raise
