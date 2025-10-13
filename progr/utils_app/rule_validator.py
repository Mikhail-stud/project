import ipaddress

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

    # 4. IP источника
    src_ip = rule_data.get("rules_ip_s", "")
    if src_ip.lower() != "any":
        try:
            ipaddress.ip_address(src_ip)
        except ValueError:
            errors.append(f"Некорректный IP-адрес источника: {src_ip}")

    # 5. Порт источника
    src_port = str(rule_data.get("rules_port_s", "")).lower()
    if src_port != "any" and not validate_port(src_port):
        errors.append(f"Некорректный порт источника: {src_port}")

    # 6. IP получателя
    dst_ip = rule_data.get("rules_ip_d", "")
    if dst_ip.lower() != "any":
        try:
            ipaddress.ip_address(dst_ip)
        except ValueError:
            errors.append(f"Некорректный IP-адрес получателя: {dst_ip}")

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