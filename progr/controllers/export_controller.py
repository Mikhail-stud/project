from progr.models.export_model import ExportModel
from progr.utils_app.export_rules import export_to_rules_file
from progr.utils_app.logger import LOGGER


class ExportController:
    """
    Контроллер для экспорта правил IDS/IPS в файл .rules.
    """

    def export_rules(self, system_type, file_path):
        """
        Экспортирует правила в файл .rules для выбранного СЗИ.
        
        :param system_type: "IDS" или "IPS"
        :param file_path: путь для сохранения файла
        :return: (успех: bool, сообщение: str)
        """
        try:
            LOGGER.info(f"[ExportController] Запрос экспорта: system_type={system_type}, file={file_path}")

            rules = ExportModel.get_rules_for_system(system_type)
            if not rules:
                msg = "Нет правил для экспорта."
                LOGGER.warning(f"[ExportController] {msg}")
                return False, msg

            export_to_rules_file(rules, file_path)
            msg = f"Экспортировано {len(rules)} правил в {file_path}"
            LOGGER.info(f"[ExportController] {msg}")
            return True, msg

        except Exception as e:
            error_msg = f"Ошибка экспорта: {e}"
            LOGGER.error(f"[ExportController] {error_msg}", exc_info=True)
            return False, error_msg