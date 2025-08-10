"""
Конфигурация интерфейса приложения (UI).
Содержит все размеры окон, заголовки и глобальные стили.
"""

UI_CONFIG = {
    # === Главное окно приложения ===
    "main_window": {
        "title": "IDS/IPS Rule Manager",
        "width": 1000,
        "height": 800
    },

    # === Диалог создания/редактирования правил ===
    "create_rule_dialog": {
        "title_create": "Создание правила",
        "title_edit": "Редактирование правила",
        "min_width": 800,
        "min_height": 600
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
        "table_alternate_row_color": "#000000FF"
    }
}
