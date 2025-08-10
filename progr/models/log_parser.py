import re
import pandas as pd
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
        """
        LOGGER.info(f"[LogParser] Парсинг Apache/Nginx логов, строк={len(lines)}")
        parsed_data = []

        for line in lines:
            match = self.apache_nginx_pattern.search(line)
            if match:
                parsed_data.append([
                    match.group("time"),
                    match.group("ip"),
                    match.group("method"),
                    match.group("object"),
                    match.group("protocol"),
                    int(match.group("code")),
                    match.group("referer"),
                    match.group("agent")
                ])

        df = pd.DataFrame(parsed_data, columns=[
            "time", "ip", "method", "object", "protocol", "code", "referer", "user_agent"
        ])
        LOGGER.info(f"[LogParser] Получено {len(df)} записей Apache/Nginx")
        return df

    def parse_wordpress(self, lines):
        """
        Пример парсинга логов WordPress (wp-login.php, wp-admin и т.д.).
        """
        LOGGER.info(f"[LogParser] Парсинг WordPress логов, строк={len(lines)}")
        parsed_data = []

        for line in lines:
            if "wp-login.php" in line or "wp-admin" in line:
                match = self.apache_nginx_pattern.search(line)
                if match:
                    parsed_data.append([
                        match.group("time"),
                        match.group("ip"),
                        match.group("method"),
                        match.group("object"),
                        match.group("protocol"),
                        int(match.group("code")),
                        match.group("referer"),
                        match.group("agent")
                    ])

        df = pd.DataFrame(parsed_data, columns=[
            "time", "ip", "method", "object", "protocol", "code", "referer", "user_agent"
        ])
        LOGGER.info(f"[LogParser] Получено {len(df)} записей WordPress")
        return df

    def parse_bitrix(self, lines):
        """
        Пример парсинга логов Bitrix (часто встречаются admin и /bitrix/).
        """
        LOGGER.info(f"[LogParser] Парсинг Bitrix логов, строк={len(lines)}")
        parsed_data = []

        for line in lines:
            if "/bitrix/" in line:
                match = self.apache_nginx_pattern.search(line)
                if match:
                    parsed_data.append([
                        match.group("time"),
                        match.group("ip"),
                        match.group("method"),
                        match.group("object"),
                        match.group("protocol"),
                        int(match.group("code")),
                        match.group("referer"),
                        match.group("agent")
                    ])

        df = pd.DataFrame(parsed_data, columns=[
            "time", "ip", "method", "object", "protocol", "code", "referer", "user_agent"
        ])
        LOGGER.info(f"[LogParser] Получено {len(df)} записей Bitrix")
        return df