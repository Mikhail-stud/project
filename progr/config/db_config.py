"""
Параметры подключения к базе данных PostgreSQL.
Используются всеми моделями (RuleModel и др.).
"""

DB_CONFIG = {
    "host": "127.0.0.1",        # адрес сервера БД
    "port": 5432,               # порт PostgreSQL
    "dbname": "proga_db",     # имя базы данных
    "user": "postgres",         # имя пользователя
    "password": "admin" # пароль пользователя
}
