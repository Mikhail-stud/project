import ipaddress
import re

# Допустимые значения для проверки
VALID_ACTIONS = {"alert", "log", "pass", "activate", "dynamic", "drop", "reject", "sdrop"}
VALID_PROTOCOLS = {"tcp", "udp", "icmp", "http"}
VALID_DIRECTIONS = {"->", "<-", "<->"}  # Направления

def validate_rule(rule_data: dict):
    """
    Проверка корректности данных правила IDS/IPS.
    :param rule_data: словарь с ключами БД и значениями полей
    :return: (bool, list) — True/False и список сообщений об ошибках
    """
    errors = []

    # 1. Действие
    action = rule_data.get("rules_action", "").lower()
    if action not in VALID_ACTIONS:
        errors.append(f"Недопустимое значение в 'Действие': {action} "
                      f"(допустимые: {', '.join(VALID_ACTIONS)})")

    # 2. Протокол
    protocol = rule_data.get("rules_protocol", "").lower()
    if protocol not in VALID_PROTOCOLS:
        errors.append(f"Недопустимый протокол: {protocol} "
                      f"(допустимые: {', '.join(VALID_PROTOCOLS)})")

    # 3. Направление
    direction = rule_data.get("rules_route", "")
    if direction not in VALID_DIRECTIONS:
        errors.append(f"Недопустимое направление: {direction} "
                      f"(допустимые: {', '.join(VALID_DIRECTIONS)})")

    # 4. IP источника (поддержка нескольких значений и CIDR)
    src_ip_raw = (str(rule_data.get("rules_ip_s", "")) or "").strip()
    if src_ip_raw:
        ok, normalized, ip_errs = _normalize_multi_ip_field(src_ip_raw)
        if not ok:
            errors.append("IP-адрес источника: " + "; ".join(ip_errs))
        else:
            # нормализуем значение обратно в rule_data (канонический вид)
            rule_data["rules_ip_s"] = normalized
            # если были частные ошибки — добавим как предупреждение (по желанию можно удалить)
            if ip_errs:
                errors.append("IP-адрес источника (предупреждения): " + "; ".join(ip_errs))
    else:
        errors.append("IP-адрес источника не указан")

    # 5. Порт источника
    src_port = str(rule_data.get("rules_port_s", "")).lower()
    if src_port != "any" and not validate_port(src_port):
        errors.append(f"Некорректный порт источника: {src_port}")

    # 6. IP получателя
    dst_ip_raw = (str(rule_data.get("rules_ip_d", "")) or "").strip()
    if dst_ip_raw:
        ok, normalized, ip_errs = _normalize_multi_ip_field(dst_ip_raw)
        if not ok:
            errors.append("IP-адрес получателя: " + "; ".join(ip_errs))
        else:
            rule_data["rules_ip_d"] = normalized
            if ip_errs:
                errors.append("IP-адрес получателя (предупреждения): " + "; ".join(ip_errs))


    # 7. Порт получателя
    dst_port = str(rule_data.get("rules_port_d", "")).lower()
    if dst_port != "any" and not validate_port(dst_port):
        errors.append(f"Некорректный порт получателя: {dst_port}")

    # 8. Название правила (msg)
    msg = rule_data.get("rules_msg", "").strip()
    if not msg:
        errors.append("Поле 'Название правила' не может быть пустым")

    # 9. Содержимое правила (content)
    content = rule_data.get("rules_content", "").strip()
    if not content:
        errors.append("Поле 'Содержимое правила' не может быть пустым")

    # 10. SID
    if not validate_positive_int(rule_data.get("rules_sid")):
        errors.append(f"Некорректный SID: {rule_data.get('rules_sid')}")

    # 11. Версия (rev)
    if not validate_positive_int(rule_data.get("rules_rev")):
        errors.append(f"Некорректная версия правила: {rule_data.get('rules_rev')}")

    return len(errors) == 0, errors


def validate_port(port):
    """Проверка порта (1-65535)"""
    try:
        port = int(port)
        return 1 <= port <= 65535
    except (ValueError, TypeError):
        return False


def validate_positive_int(value):
    """Проверка положительного целого числа"""
    try:
        return int(value) > 0
    except (ValueError, TypeError):
        return False

def _split_multi_values(s: str) -> list[str]:
    """
    Делит строку по запятым/пробелам/';'. Убирает пустые элементы, сохраняет порядок.
    """
    if not s:
        return []
    parts = re.split(r"[,\s;]+", s.strip())
    return [p for p in parts if p]

def _validate_ip_or_cidr(token: str) -> tuple[bool, str | None, str | None]:
    """
    Проверяет один токен: IP (v4/v6), CIDR-сеть (v4/v6) или 'any'.
    Возвращает (ok, normalized, error_msg).
    """
    t = token.strip()
    if not t:
        return False, None, "пустое значение"

    if t.lower() == "any":
        return True, "any", None

    # Сеть: допускаем strict=False (т.е. 192.168.1.10/24 → 192.168.1.0/24)
    if "/" in t:
        try:
            net = ipaddress.ip_network(t, strict=False)
            return True, str(net), None
        except Exception as e:
            return False, None, f"некорректная сеть: {t} ({e})"

    # Одиночный IP
    try:
        ip = ipaddress.ip_address(t)
        return True, str(ip), None
    except Exception as e:
        return False, None, f"некорректный IP: {t} ({e})"

def _normalize_multi_ip_field(raw: str) -> tuple[bool, str, list[str]]:
    """
    Валидирует поле с множеством IP/сетей/any.
    Возвращает (ok, normalized_joined, errors):
      - normalized_joined — значения через ', ' в каноническом виде, без дублей.
      - errors — список ошибок по некорректным элементам.
    Логика:
      - если есть хотя бы один валидный элемент — поле считается валидным,
        но ошибки по невалидным вернём (их можно показать пользователю).
      - если валидных нет — поле невалидно.
      - если присутствует 'any' вместе с другими, оставляем только 'any'.
    """
    tokens = _split_multi_values(raw)
    if not tokens:
        return False, "", ["не указаны IP-адреса/сети"]

    seen = set()
    normalized: list[str] = []
    errors: list[str] = []

    for t in tokens:
        ok, norm, err = _validate_ip_or_cidr(t)
        if not ok:
            errors.append(err or f"некорректное значение: {t}")
            continue
        if norm == "any":
            # 'any' доминирует — остальное не имеет смысла
            return True, "any", errors
        if norm not in seen:
            seen.add(norm)
            normalized.append(norm)

    if not normalized:
        return False, "", errors

    return True, ", ".join(normalized), errors
