import psycopg2
from psycopg2.extras import RealDictCursor
from config.db_config import DB_CONFIG
from utils.logger import LOGGER


class ExportModel:
    """
    Модель для получения правил IDS/IPS из БД с фильтрацией по rules_action.
    """

    IDS_ACTIONS = ("alert", "log", "pass", "activate", "dynamic")
    IPS_ACTIONS = ("drop", "reject", "sdrop")

    @staticmethod
    def get_rules_for_system(system_type):
        """
        Возвращает правила из БД для выбранного СЗИ.
        
        :param system_type: "IDS" или "IPS"
        :return: список словарей с данными правил
        """
        # Определяем фильтр действий
        if system_type.upper() == "IDS":
            actions = ExportModel.IDS_ACTIONS
        elif system_type.upper() == "IPS":
            actions = ExportModel.IPS_ACTIONS
        else:
            raise ValueError(f"Неизвестный тип СЗИ: {system_type}")

        query = """
        SELECT id, rules_action, rules_protocol, rules_ip_s, rules_port_s,
               rules_route, rules_ip_d, rules_port_d, rules_msg, rules_content,
               rules_sid, rules_rev
        FROM rules
        WHERE rules_action = ANY(%s)
        ORDER BY id;
        """

        try:
            LOGGER.info(f"[ExportModel] Получение правил для {system_type} (actions={actions})")
            with psycopg2.connect(**DB_CONFIG) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query, (list(actions),))
                    rules = cur.fetchall()
                    LOGGER.info(f"[ExportModel] Получено {len(rules)} правил для {system_type}")
                    return rules
        except Exception as e:
            LOGGER.error(f"[ExportModel] Ошибка получения правил для {system_type}: {e}", exc_info=True)
            raise