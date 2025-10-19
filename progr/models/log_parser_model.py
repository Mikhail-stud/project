import re
import pandas as pd
from datetime import datetime
from progr.utils_app.logger import LOGGER


class LogParser:
    """
    Модель для парсинга логов различных форматов:
    - Apache
    - Nginx
    - WordPress
    - Bitrix
    """

    # Регулярка для Apache/Nginx access log (Common Log Format + User-Agent)
    apache_nginx_pattern = re.compile(
        r'(?P<source_ip>\S+) \S+ \S+ \[(?P<time>[^\]]+)\] '
        r'"(?P<method>[A-Z]+) (?P<object>\S+) (?P<protocol>HTTP/\d(?:\.\d)?)" '
        r'(?P<code>\d{3}) (?P<size>\S+) "(?P<referer>[^"]*)" "(?P<agent>[^"]*)"'
    )

    def parse_apache_nginx(self, lines):
        """
        Парсит Apache/Nginx access logs в DataFrame.
         'time' разбивается на отдельные колонки 'date' и 'time'.
        """
        LOGGER.info(f"[LogParser] Парсинг Apache/Nginx логов, строк={len(lines)}")
        parsed_data = []

        for line in lines:
            match = self.apache_nginx_pattern.search(line)
            if match:
                raw_time = match.group("time")
                date_str, time_str = self._split_apache_time(raw_time)
                protocol = match.group("protocol")
                proto, proto_ver = self._split_protocol(protocol)

                parsed_data.append([
                    date_str,                         
                    time_str,                         
                    match.group("source_ip"),
                    match.group("method"),
                    match.group("object"),
                    protocol,
                    proto,
                    proto_ver,
                    (match.group("code")),
                    match.group("referer"),
                    match.group("agent")
                ])

        df = pd.DataFrame(parsed_data, columns=[
            "date", "time", "source_ip", "method", "object", "protocol", "proto", "proto_ver", "code", "referer", "user_agent"
        ])
        LOGGER.info(f"[LogParser] Получено {len(df)} записей Apache/Nginx")
        return df

    def parse_wordpress_activitylog(self, text) -> pd.DataFrame:
        """
        Парсер дампа WordPress activity log (кортежи в скобках).
        Возвращает DataFrame с колонками:
        ip, object, user_agent, event_type, user_roles, username, site_id, user_id
        """
        if not isinstance(text, str):
            try:
                text = "".join(text)
            except Exception:
                text = str(text)

        rows = []
        for rec in self._iter_wp_tuples(text):
            try:
                row = {
                    "source_ip":         str(rec[4]  or ""),   # №5
                    "object":     str(rec[6]  or ""),   # №7
                    "user_agent": str(rec[8]  or ""),   # №9
                    "event_type": str(rec[7]  or ""),   # №8
                    "user_roles": str(rec[9]  or ""),   # №10
                    "username":   str(rec[10] or ""),   # №11
                    "site_id":    self._to_int_or_empty_wp(rec[1]),   # №2
                    "user_id":    self._to_int_or_empty_wp(rec[11]),  # №12
                }
                rows.append(row)
            except Exception:
                continue

        df = pd.DataFrame(rows, columns=[
            "source_ip", "object", "user_agent", "event_type",
            "user_roles", "username", "site_id", "user_id"
        ])

        LOGGER.info(f"[LogParser] Получено {len(df)} записей WordPress")
        return df


    def _iter_wp_tuples(self, text: str):
        """
        Итерирует кортежи '(...)' верхнего уровня и возвращает список полей.
        Учитывает одинарные кавычки и SQL-экранирование '' внутри строк.
        """
        for tup in self._find_parenthesized(text):
            inner = tup[1:-1]
            fields = self._split_fields_sql_quotes(inner)
            norm = [self._normalize_wp_field(f) for f in fields]

            if len(norm) < 16:
                norm += [""] * (16 - len(norm))
            elif len(norm) > 16:
                norm = norm[:16]
            yield norm

    @staticmethod
    def _find_parenthesized(text: str):

        start, depth = None, 0
        for i, ch in enumerate(text):
            if ch == "(":
                if depth == 0: start = i
                depth += 1
            elif ch == ")":
                if depth > 0:
                    depth -= 1
                    if depth == 0 and start is not None:
                        yield text[start:i+1]
                        start = None

    @staticmethod
    def _split_fields_sql_quotes(s: str):


        fields, buf = [], []
        in_q = False
        i = 0
        while i < len(s):
            ch = s[i]
            if in_q:
                if ch == "'":
                    if i + 1 < len(s) and s[i + 1] == "'":  
                        buf.append("'")
                        i += 2
                        continue
                    in_q = False
                    i += 1
                    continue
                else:
                    buf.append(ch)
                    i += 1
                    continue
            else:
                if ch == "'":
                    in_q = True
                    i += 1
                    continue
                elif ch == ",":
                    fields.append("".join(buf).strip())
                    buf = []
                    i += 1
                    continue
                else:
                    buf.append(ch)
                    i += 1
        fields.append("".join(buf).strip())
        return fields

    @staticmethod
    def _normalize_wp_field(token: str):
        """
        Нормализация токенов: NULL→None, числа→int/float, остальное→str.
        """
        t = token.strip()
        if not t or t == "-":
            return ""
        if t.upper() == "NULL":
            return None
        # целое?
        if t.isdigit():
            try:
                return int(t)
            except Exception:
                pass
        # вещественное?
        try:
            if "." in t and t.replace(".", "", 1).isdigit():
                return float(t)
        except Exception:
            pass
        return t

    @staticmethod
    def _to_int_or_empty_wp(val):
        if val is None or val == "":
            return ""
        try:
            return int(val)
        except Exception:
            return ""

    def parse_bitrix_eventlog(self, text: str) -> pd.DataFrame:
        """
        Разбирает текстовую выгрузку b_event_log (кортежи в скобках, разделённые запятыми).
        Возвращает DataFrame с колонками:
        date, time, ip, object, user-agent, audit_type_id, site_id, user_id, guest_id
        """
        if not isinstance(text, str):
            try:
                text = "".join(text)
            except Exception:
                text = str(text)
        rows = []
        for rec_fields in self._iter_bitrix_tuples(text):
            # Ожидаемые позиции в b_event_log:
            #  0: ID
            #  1: TIMESTAMP_X  -> 'YYYY-MM-DD HH:MM:SS'
            #  2: SEVERITY
            #  3: AUDIT_TYPE_ID
            #  4: MODULE_ID
            #  5: ITEM_ID
            #  6: REMOTE_ADDR  -> ip
            #  7: USER_AGENT   -> user-agent
            #  8: REQUEST_URI  -> object
            #  9: SITE_ID
            # 10: USER_ID
            # 11: GUEST_ID
            # 12: DESCRIPTION
            try:
                ts = str(rec_fields[1] or "")
                date_str, time_str = (ts.split(" ", 1) + [""])[:2]
                row = {
                    "date": date_str,
                    "time": time_str,
                    "source_ip": str(rec_fields[6] or ""),
                    "object": str(rec_fields[8] or ""),
                    "user_agent": str(rec_fields[7] or ""),
                    "audit_type_id": str(rec_fields[3] or ""),
                    "site_id": str(rec_fields[9] or ""),
                    "user_id": self._to_int_or_empty(rec_fields[10]),
                    "guest_id": self._to_int_or_empty(rec_fields[11]),
                }
                rows.append(row)
            except Exception as e:
                LOGGER.warning(f"[Bitrix parser] skip malformed tuple: {e}")

        df = pd.DataFrame(rows, columns=[
            "date", "time", "source_ip", "object", "user_agent",
            "audit_type_id", "site_id", "user_id", "guest_id"
        ])

        LOGGER.info(f"[LogParser] Получено {len(df)} записей Bitrix")
        return df
    
    @staticmethod
    def _to_int_or_empty(val):
        if val is None or val == "":
            return ""
        try:
            return int(val)
        except Exception:
            return ""

    def _iter_bitrix_tuples(self, text: str):
        """
        Итерирует кортежи из b_event_log, корректно деля на поля по запятым
        с учётом одинарных кавычек и экранирования (\' внутри строки).
        Возвращает список значений.
        """
        # 1) вычленяем подстроки вида (...) — допускаем перевод строки внутри
        for tup in self._find_parenthesized(text):
            # 2) убираем скобки и парсим поля, учитывая кавычки
            inner = tup[1:-1]
            fields = self._split_fields_preserving_quotes(inner)
            # нормализуем NULL/строки/числа
            norm = [self._normalize_field(f) for f in fields]

            if len(norm) < 13:
                norm += [""] * (13 - len(norm))
            elif len(norm) > 13:
                norm = norm[:13]
            yield norm

    @staticmethod
    def _find_parenthesized(text: str):


        start = None
        depth = 0
        for i, ch in enumerate(text):
            if ch == "(":
                if depth == 0:
                    start = i
                depth += 1
            elif ch == ")":
                if depth > 0:
                    depth -= 1
                    if depth == 0 and start is not None:
                        yield text[start:i+1]
                        start = None


    @staticmethod
    def _split_fields_preserving_quotes(s: str):
        """
         Делит строку кортежа на поля по ',' с учётом одинарных кавычек.
         Поддерживает SQL-экранирование одинарной кавычки удвоением: '' → '
        """
        fields, buf = [], []
        in_q = False
        i = 0
        while i < len(s):
            ch = s[i]
            if in_q:
                if ch == "'":
                     # удвоенная кавычка внутри строки → добавляем одинарную и пропускаем вторую
                    if i + 1 < len(s) and s[i + 1] == "'":
                        buf.append("'")
                        i += 2
                        continue
                     # конец строки
                    in_q = False
                    i += 1
                    continue
                else:
                    buf.append(ch)
                    i += 1
                    continue
            else:
                if ch == "'":
                    in_q = True
                    i += 1
                    continue
                elif ch == ",":
                    fields.append("".join(buf).strip())
                    buf = []
                    i += 1
                    continue
                else:
                    buf.append(ch)
                    i += 1
        fields.append("".join(buf).strip())
        return fields

    @staticmethod
    def _normalize_field(token: str):
        """
        Преобразует токен поля:
          - 'NULL'  -> None
          - '123'   -> 123 (int)
          - '...'(в кавычках) -> строка (с уже снятыми кавычками на предыдущем шаге)
          - пустые/дефисы -> ""
        """
        t = token.strip()
        if not t or t == "-":
            return ""
        # Токены, обрамлённые кавычками, на предыдущем шаге уже без кавычек
        # Здесь 'NULL' (в любом регистре) трактуем как None
        if t.upper() == "NULL":
            return None
        # Попробуем число
        if t.isdigit():
            try:
                return int(t)
            except Exception:
                return t
        return t


    @staticmethod
    def _split_apache_time(raw: str) -> tuple[str, str]:
        """
        Разбирает время вида '27/Jul/2025:07:55:25 +0700' на ('YYYY-MM-DD', 'HH:MM:SS'),

        
        Возвращает ("", исходная_строка), если распарсить не удалось.
        """
        if not raw:
            return "", ""
        s = str(raw).strip()

    # Ожидаем формат: DD/Mon/YYYY:HH:MM:SS ±ZZZZ

        parts = s.split(" ", 1)
        core = parts[0]  # '27/Jul/2025:07:55:25'


    # DD/Mon/YYYY:HH:MM:SS
        try:
            day_str, mon_str, rest = core.split("/", 2)           # '27', 'Jul', '2025:07:55:25'
            year_str, hh, mm, ss = rest.split(":", 3)             # '2025', '07', '55', '25'

            mon_map = {
            "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
            "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
            "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12",
            }
            mon = mon_map.get(mon_str, None)
            if mon is None:
            # неожиданный месяц — падаем в except
                raise ValueError(f"Unknown month: {mon_str}")

        # Нормализуем компоненты
            day = day_str.zfill(2)
            year = year_str

            date_str = f"{year}-{mon}-{day}"
            time_str = f"{hh.zfill(2)}:{mm.zfill(2)}:{ss.zfill(2)}"
            return date_str, time_str

        except Exception:

            return "", s
    @staticmethod
    def _split_protocol(proto_raw: str) -> tuple[str, str]:
        """
        'HTTP/1.1' -> ('HTTP', '1.1'), 'HTTP/2' -> ('HTTP', '2'), иначе ('', '')
        """
        if not proto_raw:
            return "", ""
        parts = str(proto_raw).split("/", 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        return str(proto_raw), ""
