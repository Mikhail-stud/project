"""
Конфигурация интерфейса приложения (UI).
Содержит все размеры окон, заголовки и глобальные стили.
"""

UI_CONFIG = {
    # === Главное окно приложения ===
    "main_window": {
        "title": "IDS/IPS Rule Manager",
        "width": 800,
        "height": 600
    },

    # === Диалог создания/редактирования правил ===
    "create_rule_dialog": {
        "title_create": "Создание правила",
        "title_edit": "Редактирование правила",
        "min_width": 600,
        "min_height": 400
    },

    # === Цвета подсветки HTTP-кодов ===
    "http_colors": {
        "success": "#0fa80f",  # 2xx — зелёный
        "error": "#d40000"     # 4xx/5xx — красный
    },

    # === Общие стили ===
    "styles": {
        "font": "Arial",
        "font_size": 10,
        "table_alternate_row_color": "#685F5F"
    }
}