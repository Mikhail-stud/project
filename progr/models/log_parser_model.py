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
        r'(?P<ip>\S+) \S+ \S+ \[(?P<time>[^\]]+)\] '
        r'"(?P<method>[A-Z]+) (?P<object>\S+) (?P<protocol>HTTP/\d\.\d)" '
        r'(?P<code>\d{3}) (?P<size>\S+) "(?P<referer>[^"]*)" "(?P<agent>[^"]*)"'
    )

    def parse_apache_nginx(self, lines):
        """
        Парсит Apache/Nginx access logs в DataFrame.
        Теперь 'time' разбивается на отдельные колонки 'date' и 'time'.
        """
        LOGGER.info(f"[LogParser] Парсинг Apache/Nginx логов, строк={len(lines)}")
        parsed_data = []

        for line in lines:
            match = self.apache_nginx_pattern.search(line)
            if match:
                raw_time = match.group("time")
                date_str, time_str = self._split_apache_time(raw_time)

                parsed_data.append([
                    date_str,                         # 'date'  <-- НОВОЕ
                    time_str,                         # 'time'  <-- обновлённое (HH:MM:SS)
                    match.group("ip"),
                    match.group("method"),
                    match.group("object"),
                    match.group("protocol"),
                    int(match.group("code")),
                    match.group("referer"),
                    match.group("agent")
                ])

        df = pd.DataFrame(parsed_data, columns=[
            "date", "time", "ip", "method", "object", "protocol", "code", "referer", "user_agent"
        ])
        LOGGER.info(f"[LogParser] Получено {len(df)} записей Apache/Nginx")
        return df

    def parse_wordpress(self, lines):
        """
        Пример парсинга логов WordPress (wp-login.php, wp-admin и т.д.).
        Теперь возвращаем 'date' и 'time' отдельно, как в Apache/Nginx.
        """
        LOGGER.info(f"[LogParser] Парсинг WordPress логов, строк={len(lines)}")
        parsed_data = []

        for line in lines:
            if "wp-login.php" in line or "wp-admin" in line:
                match = self.apache_nginx_pattern.search(line)
                if match:
                    raw_time = match.group("time")
                    date_str, time_str = self._split_apache_time(raw_time)

                    parsed_data.append([
                        date_str, time_str,
                        match.group("ip"),
                        match.group("method"),
                        match.group("object"),
                        match.group("protocol"),
                        int(match.group("code")),
                        match.group("referer"),
                        match.group("agent")
                    ])

        df = pd.DataFrame(parsed_data, columns=[
            "date", "time", "ip", "method", "object", "protocol", "code", "referer", "user_agent"
        ])
        LOGGER.info(f"[LogParser] Получено {len(df)} записей WordPress")
        return df


    def parse_bitrix(self, lines):
        """
        Пример парсинга логов Bitrix (часто встречаются admin и /bitrix/).
        Теперь возвращаем 'date' и 'time' отдельно, как в Apache/Nginx.
        """
        LOGGER.info(f"[LogParser] Парсинг Bitrix логов, строк={len(lines)}")
        parsed_data = []

        for line in lines:
            if "/bitrix/" in line:
                match = self.apache_nginx_pattern.search(line)
                if match:
                    raw_time = match.group("time")
                    date_str, time_str = self._split_apache_time(raw_time)

                    parsed_data.append([
                        date_str, time_str,
                        match.group("ip"),
                        match.group("method"),
                        match.group("object"),
                        match.group("protocol"),
                        int(match.group("code")),
                        match.group("referer"),
                        match.group("agent")
                    ])

        df = pd.DataFrame(parsed_data, columns=[
            "date", "time", "ip", "method", "object", "protocol", "code", "referer", "user_agent"
        ])
        LOGGER.info(f"[LogParser] Получено {len(df)} записей Bitrix")
        return df

    @staticmethod
    def _split_apache_time(raw: str) -> tuple[str, str]:
        """
        Разбирает время вида '27/Jul/2025:07:55:25 +0700' на ('YYYY-MM-DD', 'HH:MM:SS'),
        НЕ завися от локали ОС.

        Возвращает ("", исходная_строка), если распарсить не удалось.
        """
        if not raw:
            return "", ""
        s = str(raw).strip()

    # Ожидаем формат: DD/Mon/YYYY:HH:MM:SS ±ZZZZ
    # Разделим на основную часть и смещение часового пояса (offset нам тут не нужно).
        parts = s.split(" ", 1)
        core = parts[0]  # '27/Jul/2025:07:55:25'
    # offset = parts[1] if len(parts) > 1 else None  # если когда-нибудь понадобится

    # DD/Mon/YYYY:HH:MM:SS
        try:
            day_str, mon_str, rest = core.split("/", 2)           # '27', 'Jul', '2025:07:55:25'
            year_str, hh, mm, ss = rest.split(":", 3)             # '2025', '07', '55', '25'
        # Месяцы — английские аббревиатуры, не зависят от локали
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
        # Фолбэк: не ломаемся — вернём исходную строку во 'time', а 'date' оставим пустой
            return "", s