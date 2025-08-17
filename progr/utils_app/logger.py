import logging
import os
from datetime import datetime

# === Создаём папку для логов ===
LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# === Создаём логгер ===
LOGGER = logging.getLogger("Programm_X_Logger")
LOGGER.setLevel(logging.DEBUG)  # Логируем всё, фильтрация на хендлерах

# === Имя файла лога с датой ===
log_filename = datetime.now().strftime("app_%Y-%m-%d.log")
log_path = os.path.join(LOG_DIR, log_filename)


# === Формат логов ===
formatter = logging.Formatter(
    fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# === Обработчик для файла ===
file_handler = logging.FileHandler(log_path, encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# === Обработчик для консоли ===
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# === Добавляем обработчики ===
if not LOGGER.handlers:  # Чтобы не дублировать обработчики при повторных импортах
    LOGGER.addHandler(file_handler)
    LOGGER.addHandler(console_handler)

LOGGER.info("Логгер инициализирован. Логи пишутся в %s", log_path)