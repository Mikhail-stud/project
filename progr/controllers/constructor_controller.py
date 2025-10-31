from progr.threads.log_parser_thread import LogParserThread
from progr.models.logs_table_model import LogsTableModel
from progr.models.rule_model import RuleModel
from progr.utils_app.logger import LOGGER
import pandas as pd
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox


class ConstructorController:
    """
    Контроллер вкладки 'Конструктор':
    - Асинхронный парсинг логов (создаёт LogParserThread)
    - Создаёт табличную модель логов с чекбоксами В ЯЧЕЙКАХ.
    - Формирует prefill-словарь для диалога создания правила по отмеченным ячейкам.
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

        КАК МЕНЯТЬ/ДОБАВЛЯТЬ СТОЛБЦЫ:
          1) Измени список headers ниже (порядок = порядок в таблице).
          2) В build_prefill_from_selection НИЖЕ поправь словарь col_to_field.
        """
        if df is None:
            df = pd.DataFrame()

        # ВАЖНО: названия колонок в DataFrame должны совпадать со списком headers
        headers = ["date", "time", "source_ip", "method", "object", "protocol", "code", "referer", "user_agent", "audit_type_id", "site_id",
                    "user_id", "guest_id", "event_type", "user_roles", "username"]

        safe_df = df.reindex(columns=headers, fill_value="")

        rows = safe_df.values.tolist()
        model = LogsTableModel(rows, headers, parent=parent)

        LOGGER.info("[ConstructorController] Создана LogsTableModel: rows=%s, cols=%s",
                    len(rows), len(headers))
        return model

    def _headers_from_model(self, model: LogsTableModel) -> list[str]:
        """
        Универсально достаём список заголовков из модели, вне зависимости от реализации.
        """
        cols = model.columnCount()
        headers = []
        for c in range(cols):
            h = model.headerData(c, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
            headers.append(str(h) if h is not None else "")
        return headers

    def _get_checked_values_by_column(self, model: LogsTableModel, col: int) -> list[str]:
        """
        Универсально получаем отмеченные значения в колонке:
        - Если у модели есть метод get_checked_values_by_column — используем его.
        - Иначе делаем безопасный обход вручную по CheckStateRole.
        """
        if hasattr(model, "get_checked_values_by_column"):
            try:
                return [str(v) for v in model.get_checked_values_by_column(col)]
            except Exception:
                pass

        # Фолбэк: проходим все строки и смотрим CheckStateRole каждой ячейки
        values = []
        rows = model.rowCount()
        for r in range(rows):
            idx = model.index(r, col)
            state = model.data(idx, Qt.ItemDataRole.CheckStateRole)
            try:
                state = Qt.CheckState(state)
            except Exception:
                state = Qt.CheckState.Unchecked
            if state == Qt.CheckState.Checked:
                val = model.data(idx, Qt.ItemDataRole.DisplayRole)
                val = "" if val is None else str(val).strip()
                if val:
                    values.append(val)
        return values

    def build_prefill_from_selection(self, model: LogsTableModel) -> dict:
        """
         Формирует данные для предзаполнения диалога «Создать правило»
         из ОТМЕЧЕННЫХ чекбоксов в ячейках.
         """
        headers = []
        if hasattr(model, "headers"):
            h = getattr(model, "headers")
            try:
                headers = list(h()) if callable(h) else list(h)
            except Exception:
                headers = []
        if not headers:
            headers = self._headers_from_model(model)
 
          # === МАППИНГ: колонка таблицы -> поле диалога ===
        col_to_field: dict[str, str | None] = {
             "source_ip": "rules_ip_s",
             "protocol": "rules_content",
             "method": "rules_content",
             "object": "rules_content",
             "date": None,
             "time": None,
             "code": "rules_content",
             "referer": "rules_content",
             "user_agent": "rules_content",   
             "audit_type_id": None,
             "site_id": None,
             "user_id": None,
             "guest_id": None,
             "event_type": None,
             "user_roles": None,
             "username": None,
        }
 
         # накапливаем значения по каждому полю диалога
        buckets: dict[str, list[str]] = {}
 
        for col_index, col_name in enumerate(headers):
            field_key = col_to_field.get(col_name)
            if not field_key:
                continue
            values = self._get_checked_values_by_column(model, col_index)
            if not values:
                continue
            buckets.setdefault(field_key, [])
             # приводим к строке и добавляем
            buckets[field_key].extend(str(v).strip() for v in values if str(v).strip())
 
         # формируем итоговый prefill: для списковых полей склеиваем,
         # для одиночных — берём первый элемент
        prefill: dict = {}
        MULTI_FIELDS = {"rules_content", "rules_ip_s"}
        for field_key, vals in buckets.items():
             # убираем дубликаты, сохраняя порядок
            seen = set()
            uniq = [v for v in vals if not (v in seen or seen.add(v))]
            if field_key in MULTI_FIELDS:
                prefill[field_key] = ", ".join(uniq)
            else:
                prefill[field_key] = uniq[0] if uniq else ""



        LOGGER.info("[ConstructorController] Prefill из отмеченных ячеек: %s", prefill)
        return prefill

    def create_rule(self, rule_data: dict) -> bool:
        """
        Создание правила:
        - если SID уже существует -> предложить ближайший свободный из диапазона 7000000–7999999
        - если SID новый         -> создаём с rules_rev = 1
        """
        sid = rule_data.get("rules_sid") or rule_data.get("sid")
        if sid is None or str(sid).strip() == "":
            LOGGER.error("[ConstructorController] SID пуст — правило не создано")
            QMessageBox.critical(None, "Ошибка", "SID пуст. Укажите значение SID.")
            return False

        try:
            sid = int(str(sid).strip())
        except ValueError:
            QMessageBox.critical(None, "Ошибка", f"Некорректный SID: {sid}")
            return False

        # ✅ Гарантируем, что SID находится в тестовом диапазоне
        if sid < 7000000 or sid > 7999999:
            QMessageBox.warning(
                None,
                "Некорректный SID",
                "Все тестовые SID должны быть в диапазоне 7000000–7999999.\n"
                "Будет предложено ближайшее доступное значение."
            )
            sid = 7000000

        try:
            # Проверяем наличие правила с таким SID
            existing = RuleModel.get_rule_by_sid(sid)
            if existing:
                LOGGER.warning(f"[ConstructorController] Правило с SID={sid} уже существует")

                # === 🔍 Ищем ближайший свободный SID ===
                suggested = RuleModel.find_next_free_test_sid(start_sid=sid)
                if suggested:
                    res = QMessageBox.question(
                        None,
                        "SID занят",
                        f"SID {sid} уже используется.\n"
                        f"Предложить ближайший свободный: {suggested}?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if res == QMessageBox.StandardButton.Yes:
                        sid = suggested
                        rule_data["rules_sid"] = str(sid)
                        LOGGER.info(f"[ConstructorController] Пользователь выбрал предложенный SID={sid}")
                    else:
                        LOGGER.info("[ConstructorController] Пользователь отказался от замены SID")
                        return False
                else:
                    QMessageBox.critical(None, "Ошибка", "Нет доступных SID в диапазоне 7000000–7999999.")
                    return False

            # Вставляем новое правило с версией 1
            rule_data = dict(rule_data)
            rule_data["rules_sid"] = str(sid)
            rule_data["rules_rev"] = 1
            new_id = RuleModel.add_rule(rule_data)

            LOGGER.info(f"[ConstructorController] Создано правило ID={new_id} с SID={sid}, rev=1")
            QMessageBox.information(None, "Создание правила", f"Правило успешно создано.\nSID: {sid}")
            return True

        except Exception as e:
            LOGGER.error(f"[ConstructorController] Ошибка при создании правила: {e}", exc_info=True)
            QMessageBox.critical(None, "Ошибка", str(e))
            return False