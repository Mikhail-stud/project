from PyQt6.QtCore import QAbstractTableModel, Qt, QModelIndex
from PyQt6.QtGui import QColor
from typing import Any, List, Sequence, Union


class LogsTableModel(QAbstractTableModel):
    """
    Универсальная модель для таблицы логов.
    Поддерживает:
      - rows как список списков ИЛИ список словарей (второе — авто-нормализация по headers)
      - безопасные DisplayRole / EditRole
      - сортировку (override sort) c begin/endResetModel()
      - подсветку HTTP-кодов (2xx — зелёный, 4xx/5xx — красный)
      - обновление данных без пересоздания модели (update())
    """

    def __init__(
        self,
        rows: Union[List[Sequence[Any]], List[dict]],
        headers: List[str],
        parent=None
    ):
        super().__init__(parent)
        self._headers: List[str] = list(headers or [])
        # Нормализуем строки (списки/словари -> список списков по headers)
        self._rows: List[List[Any]] = self._normalize_rows(rows, self._headers)

        # Кеш позиции столбца с кодом, если он есть
        self._code_col = self._find_code_column(self._headers)

    
    # Базовые размеры модели
    
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._headers)

    # Данные
    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None

        r = index.row()
        c = index.column()

        # Безопасные границы
        if r < 0 or r >= len(self._rows) or c < 0 or c >= len(self._headers):
            return None

        value = self._rows[r][c] if c < len(self._rows[r]) else ""

        # Что показываем в ячейке
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            # Преобразуем None к пустой строке, чтобы не показывать "None"
            return "" if value is None else str(value)

        # Выравнивание — по желанию: метод, код — по центру
        if role == Qt.ItemDataRole.TextAlignmentRole:
            header = self._headers[c].lower()
            if header in ("method", "code"):
                return int(Qt.AlignmentFlag.AlignCenter)
            return int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # Подсветка по HTTP-коду
        if role == Qt.ItemDataRole.BackgroundRole and self._code_col is not None and c == self._code_col:
            code = self._as_int(value)
            if code is not None:
                if 200 <= code <= 299:
                    return QColor(210, 255, 210)  # зелёный для 2xx
                if 400 <= code <= 599:
                    return QColor(255, 220, 220)  # красный для 4xx/5xx

        # Можно добавить ToolTip на ячейки user_agent/object
        if role == Qt.ItemDataRole.ToolTipRole:
            header = self._headers[c].lower()
            if header in ("object", "user_agent", "referer"):
                return "" if value is None else str(value)

        return None

    # Заголовки
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if role != Qt.ItemDataRole.DisplayRole:
            return None

        if orientation == Qt.Orientation.Horizontal:
            if 0 <= section < len(self._headers):
                return self._headers[section]
            return None

        if orientation == Qt.Orientation.Vertical:
            # Нумерация строк с 1
            return str(section + 1)

        return None

    # Флаги редактирования
    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        # По умолчанию — только выбор (не редактируем в таблице логов)
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled


    # Сортировка
    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder) -> None:
        if not (0 <= column < len(self._headers)):
            return

        self.layoutAboutToBeChanged.emit()
        try:
            reverse = order == Qt.SortOrder.DescendingOrder

            def key_func(row):
                val = row[column] if column < len(row) else ""
                # Пытаемся сортировать код как число
                if column == self._code_col:
                    ival = self._as_int(val)
                    return (ival if ival is not None else -1)
                return str(val) if val is not None else ""

            self._rows.sort(key=key_func, reverse=reverse)
        finally:
            self.layoutChanged.emit()


    # Публичные методы обновления
    def update(self, rows: Union[List[Sequence[Any]], List[dict]], headers: List[str] | None = None) -> None:
        """
        Полная замена данных в модели.
        Если переданы новые headers — переопределяются, иначе остаются прежними.
        """
        self.beginResetModel()
        if headers is not None:
            self._headers = list(headers)
        self._rows = self._normalize_rows(rows, self._headers)
        self._code_col = self._find_code_column(self._headers)
        self.endResetModel()

    # Вспомогательные
    @staticmethod
    def _as_int(val: Any) -> int | None:
        try:
            return int(str(val).strip())
        except Exception:
            return None

    @staticmethod
    def _normalize_rows(
        rows: Union[List[Sequence[Any]], List[dict]],
        headers: List[str]
    ) -> List[List[Any]]:
        """
        Приводит входные rows к виду List[List], опираясь на headers.
        Поддержка:
          - rows = [ [..], [..], ... ]
          - rows = [ {"time":..., "ip":...}, {...}, ... ]
        Отсутствующие значения => "" (пустая строка).
        """
        if not rows:
            return []

        # Если уже список списков
        if rows and not isinstance(rows[0], dict):
            # Гарантируем, что каждая строка имеет не меньше колонок, чем headers
            out = []
            for r in rows:
                r = list(r)
                if len(r) < len(headers):
                    r = r + [""] * (len(headers) - len(r))
                out.append(r[: len(headers)])
            return out

        # Если словари — собираем по headers
        out: List[List[Any]] = []
        for d in rows:
            row = []
            for h in headers:
                row.append(d.get(h, ""))
            out.append(row)
        return out

    @staticmethod
    def _find_code_column(headers: List[str]) -> int | None:
        """
        Ищем номер столбца 'code' (без учёта регистра).
        Возвращаем индекс или None.
        """
        for i, h in enumerate(headers):
            if str(h).strip().lower() == "code":
                return i
        return None
