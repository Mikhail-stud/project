from progr.threads.log_parser_thread import LogParserThread
from progr.models.logs_table_model import  LogsTableModel
from progr.models.rule_model import RuleModel
from progr.utils_app.logger import LOGGER
import pandas as pd
from PyQt6.QtCore import Qt



class ConstructorController:
    """
    Контроллер вкладки 'Конструктор':
    - Асинхронный парсинг логов (создаёт LogParserThread)
    - Создаёт табличную модель логов с чекбоксами.
    - Формирует prefill-словарь для диалога создания правила по отмеченным колонкам/строкам.
    """

    def __init__(self):
        self._parser_thread = None

    def start_log_parse(self, log_lines, log_type, thread_starter, on_finished, on_error):
        """
        Запускает парсинг логов в отдельном потоке.
        :param log_lines: список строк логов
        :param log_type: 'apache' | 'nginx' | 'wordpress' | 'bitrix' (или др.)
        :param thread_starter: функция запуска потоков (обычно MainWindow.start)
        :param on_finished: коллбек pandas.DataFrame -> None
        :param on_error: коллбек str -> None
        """
        try:
            LOGGER.info(f"[ConstructorController] start_log_parse: type={log_type}, lines={len(log_lines)}")
            self._parser_thread = LogParserThread(log_lines, log_type)

            def _done(df):
                LOGGER.info(f"[ConstructorController] Парсинг завершён, записей: {len(df)}")
                self._parser_thread = None
                on_finished(df)

            def _err(msg):
                LOGGER.error(f"[ConstructorController] Ошибка парсинга: {msg}")
                self._parser_thread = None
                on_error(msg)

            self._parser_thread.finished.connect(_done)
            self._parser_thread.error.connect(_err)

            # поток запускает контроллер
            thread_starter(self._parser_thread)

        except Exception as e:
            LOGGER.error(f"[ConstructorController] Не удалось запустить LogParserThread: {e}", exc_info=True)
            on_error(str(e))

    def create_logs_model(self, df: pd.DataFrame, parent=None):
        """
        Создаёт и возвращает модель таблицы логов (LogsTableModel).
        Контроллер нормализует столбцы и формирует rows/headers.

        :param df: pandas.DataFrame с результатом парсинга
        :param parent: родитель для Qt-модели (обычно self из View), чтобы модель не собрал GC
        :return: (model, safe_df)
        Нормализует df под нужные колонки и создаёт LogsTableModel (с чекбоксами).
        КАК МЕНЯТЬ НАЗВАНИЯ/ДОБАВЛЯТЬ СТОЛБЦЫ:
          — редактируй список headers ниже. Порядок в таблице = порядок в этом списке.
          — добавил новый столбец => добавь его в mapping (ниже) для предзаполнения, если нужно.
        """
        if df is None:
            df = pd.DataFrame()

        headers = ["time", "ip", "method", "object", "protocol", "code", "referer", "user_agent"]
        # безопасное выравнивание нужных колонок
        safe_df = df.reindex(columns=headers, fill_value="")

        rows = safe_df.values.tolist()
        model = LogsTableModel(rows, headers, parent=parent)

        LOGGER.info("[ConstructorController] Создана LogsTableModel: rows=%s, cols=%s",
                    len(rows), len(headers))
        return model
    
    def build_prefill_from_selection(self, model: LogsTableModel) -> dict:
        """
        На основе отмеченных столбцов и строк формирует prefill-данные для диалога:
        - Берём выбранные столбцы (по заголовкам).
        - Берём выбранные строки (индексы).
        - Для каждого выбранного столбца и строки — значение из ячейки.
        - Значения записываем в поля диалога по маппингу ниже.
        Если для столбца нет соответствующего поля — пропускаем.
        """
        selected_cols = model.checked_columns()
        selected_rows = model.checked_rows()
        headers = model.headers()

        # МАППИНГ: название столбца -> поле диалога
        # Добавляй здесь соответствия новых столбцов полям диалога (если нужно автозаполнение).
        col_to_field = {
            "ip": "rules_ip_s",         # например, ip источника
            "protocol": "rules_protocol",
            "method": "rules_content",      # это пример; подставь правильно под свой диалог
            "object": None,  # сюда может собираться content
            "time": None,               # None — значит пропускаем (нет поля)
            "code": None,
            "referer": None,
            "user_agent": None,
        }

        prefill: dict = {}

        for c in selected_cols:
            if not (0 <= c < len(headers)):
                continue
            col_name = headers[c]
            field_key = col_to_field.get(col_name)
            if not field_key:
                continue

            # собираем значения по отмеченным строкам
            values = []
            for r in selected_rows:
                # вытаскиваем то, что показывает модель (DisplayRole)
                idx = model.index(r, c)
                val = model.data(idx, Qt.ItemDataRole.DisplayRole)
                if val is None:
                    val = ""
                val = str(val).strip()
                if val:
                    values.append(val)

            if not values:
                continue

            # Правило заполнения:
            # - для rules_content склеим через ', ' (потом твой парсер content разнесёт)
            # - для остальных полей возьмём первое значение
            if field_key == "rules_content":
                prefill[field_key] = ", ".join(values)
            else:
                prefill[field_key] = values[0]

        LOGGER.info("[ConstructorController] Prefill из выбора: %s", prefill)
        return prefill



    def create_rule(self, rule_data):
        
        """
        Запускает модель для создания нового правила.
        """
                
        LOGGER.info("[ConstructorController] Запуск создания нового правила")
        RuleModel.add_rule(rule_data)

