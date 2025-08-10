def export_to_rules_file(rules, file_path):
    """
    Экспортирует список правил в файл .rules.
    Формат записи:
    <action> <protocol> <src_ip> <src_port> <direction> <dst_ip> <dst_port> (msg:"..."; content:"..."; ...; sid:X; rev:Y;)

    - Если в rules_content несколько значений через запятую, каждое записывается отдельно:
      content:"значение1"; content:"значение2";
    """
    with open(file_path, "w", encoding="utf-8") as f:
        for rule in rules:
            # Базовая часть правила
            base = (
                f"{rule['rules_action']} {rule['rules_protocol']} {rule['rules_ip_s']} {rule['rules_port_s']} "
                f"{rule['rules_route']} {rule['rules_ip_d']} {rule['rules_port_d']} "
            )

            # Список параметров внутри скобок
            parts = []

            # Сообщение
            if rule.get("rules_msg"):
                parts.append(f'msg:"{rule["rules_msg"]}"')

            # Обработка rules_content
            if rule.get("rules_content"):
                # Разделяем по запятым, убираем пробелы
                contents = [c.strip() for c in rule["rules_content"].split(",") if c.strip()]
                for content in contents:
                    parts.append(f'content:"{content}"')

            # SID
            if rule.get("rules_sid") is not None:
                parts.append(f"sid:{rule['rules_sid']}")

            # REV
            if rule.get("rules_rev") is not None:
                parts.append(f"rev:{rule['rules_rev']}")

            # Финальная строка правила
            rule_str = base + "(" + "; ".join(parts) + ";)"
            f.write(rule_str + "\n")