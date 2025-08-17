from progr.models.log_parser_model import LogParser
from progr.models.logs_table_model import LogsTableModel
from progr.models.rule_model import RuleModel
from progr.utils_app.rule_validator import validate_rule
from progr.utils_app.logger import LOGGER


class ConstructorController:
    """
    Контроллер вкладки 'Конструктор'.
    Отвечает за парсинг логов и создание новых правил IDS/IPS.
    """

    def __init__(self):
        self.parser = LogParser()

    def parse_logs(self, lines, log_type):
        """
        Парсит логи в DataFrame по выбранному типу.
        :param lines: список строк логов
        :param log_type: тип логов (apache, nginx, wordpress, bitrix)
        :return: pandas DataFrame
        """
        try:
            LOGGER.info(f"[ConstructorController] Парсинг логов: тип={log_type}, строк={len(lines)}")

            if log_type in ("apache", "nginx"):
                df = self.parser.parse_apache_nginx(lines)
            elif log_type == "wordpress":
                df = self.parser.parse_wordpress(lines)
            elif log_type == "bitrix":
                df = self.parser.parse_bitrix(lines)
            else:
                raise ValueError(f"Неизвестный тип логов: {log_type}")

            LOGGER.info(f"[ConstructorController] Парсинг завершён: записей={len(df)}")
            return df

        except Exception as e:
            LOGGER.error(f"[ConstructorController] Ошибка при парсинге логов: {e}", exc_info=True)
            raise

    def create_rule(self, rule_data):
        """
        Создаёт новое правило в БД с предварительной валидацией.
        :param rule_data: словарь с данными правила (ключи = поля БД)
        :return: ID нового правила
        :raises ValueError: если валидация не пройдена
        """
        LOGGER.info(f"[ConstructorController] Попытка создания правила: {rule_data}")

        # Валидация
        is_valid, errors = validate_rule(rule_data)
        if not is_valid:
            LOGGER.warning(f"[ConstructorController] Ошибка валидации: {errors}")
            raise ValueError("\n".join(errors))

        try:
            rule_id = RuleModel.add_rule(rule_data)
            LOGGER.info(f"[ConstructorController] Новое правило создано: ID={rule_id}")
            return rule_id

        except Exception as e:
            LOGGER.error(f"[ConstructorController] Ошибка сохранения правила в БД: {e}", exc_info=True)
            raise


    def table_logs(self, rows, headers):

        LOGGER.info("[ConstructorController] Запуск создания таблицы логов")
        LogsTableModel(rows, headers)