from PyQt6.QtCore import QAbstractTableModel, Qt, QModelIndex, QVariant
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
      Табличная модель логов с чекбоксами:
      • Горизонтальный заголовок (столбцы) — чекбоксы для выбора колонок.
      • Вертикальный заголовок (строки) — чекбоксы для выбора строк.
    Публичное API:
      - toggle_column_checked(col: int), is_column_checked(col: int)
      - toggle_row_checked(row: int), is_row_checked(row: int)
      - checked_columns() -> list[int], checked_rows() -> list[int]
      - headers() -> list[str]
      - update(rows, headers=None)
    Подсветка: HTTP code — 2xx зелёный, 4xx/5xx красный.
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

        # состояния чекбоксов
        self._col_checked = [False] * len(self._headers)
        self._row_checked = [False] * len(self._rows)

        # Кеш позиции столбца с кодом, если он есть
        self._code_col = self._find_code_column(self._headers)

    
    # Базовые размеры модели
    
    def rowCount(self, parent = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._headers)

    # Данные ячеек
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
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        print(f"headerData called {section} {orientation.name if hasattr(orientation, 'name') else orientation} {int(role)}")
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self._headers[section]
            else:
                return str(section + 1)
        if role == Qt.ItemDataRole.CheckStateRole:
            state = Qt.CheckState.Checked if (0 <= section < len(self._col_checked) and self._col_checked[section]) else Qt.CheckState.Unchecked
            print(f"->returning CheckStateRole for section ={section}, orientation={'H' if orientation==Qt.Orientation.Horizontal else 'V'} => {state.value}")
            return state
            #if orientation == Qt.Orientation.Horizontal:
            # вернёт Qt.CheckState.Checked или Qt.CheckState.Unchecked
                #return Qt.CheckState.Checked if self._col_checked[section] else Qt.CheckState.Unchecked
            #else:
                #return Qt.CheckState.Checked if self._row_checked[section] else Qt.CheckState.Unchecked
        return None

    def setHeaderData(self, section, orientation, value, role=Qt.ItemDataRole.EditRole):
        # Обработка установки CheckState из заголовка (CheckableHeaderView вызывает это)
        if role == Qt.ItemDataRole.CheckStateRole:
            new_state = (value == Qt.CheckState.Checked)
            if orientation == Qt.Orientation.Horizontal:
                if 0 <= section < len(self._col_checked):
                    if self._col_checked[section] != new_state:
                        self._col_checked[section] = new_state
                        print(f"setHeaderData: horizontal section {section} set to {new_state}")
                        self.headerDataChanged.emit(Qt.Orientation.Horizontal, section, section)
                        return True
            else:
                if 0 <= section < len(self._row_checked):
                    if self._row_checked[section] != new_state:
                        self._row_checked[section] = new_state
                        print(f"setHeaderData: vertical section {section} set to {new_state}")
                        self.headerDataChanged.emit(Qt.Orientation.Vertical, section, section)
                        return True
        return False



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
        reverse = order == Qt.SortOrder.DescendingOrder
        

        def key_func(row):
            val = row[column] if column < len(row) else ""
            # Пытаемся сортировать код как число
            if column == self._code_col:
                ival = self._as_int(val)
                return (ival if ival is not None else -1)
            return str(val) if val is not None else ""

        self._rows.sort(key=key_func, reverse=reverse)
        # сортировка меняет порядок строк: синхронизируем чекбоксы строк
        self._row_checked = self._row_checked[:len(self._rows)]
        self.layoutChanged.emit()


    #  публичное API 
    def toggle_column_checked(self, col: int) -> None:
        if 0 <= col < len(self._col_checked):
            self._col_checked[col] = not self._col_checked[col]
            # уведомим заголовок
            self.headerDataChanged.emit(Qt.Orientation.Horizontal, col, col)

    def toggle_row_checked(self, row: int) -> None:
        if 0 <= row < len(self._row_checked):
            self._row_checked[row] = not self._row_checked[row]
            self.headerDataChanged.emit(Qt.Orientation.Vertical, row, row)

    def is_column_checked(self, col: int) -> bool:
        return 0 <= col < len(self._col_checked) and self._col_checked[col]

    def is_row_checked(self, row: int) -> bool:
        return 0 <= row < len(self._row_checked) and self._row_checked[row]

    def checked_columns(self) -> List[int]:
        return [i for i, v in enumerate(self._col_checked) if v]

    def checked_rows(self) -> List[int]:
        return [i for i, v in enumerate(self._row_checked) if v]

    def headers(self) -> List[str]:
        return list(self._headers)

    def update(self, rows: Union[List[Sequence[Any]], List[dict]], headers: List[str] | None = None) -> None:
        self.beginResetModel()
        if headers is not None:
            self._headers = list(headers)
        self._rows = self._normalize_rows(rows, self._headers)
        self._code_col = self._find_code_column(self._headers)
        self._col_checked = [False] * len(self._headers)
        self._row_checked = [False] * len(self._rows)
        self.endResetModel()

    # -------- utils --------
    @staticmethod
    def _as_int(val: Any) -> int | None:
        try:
            return int(str(val).strip())
        except Exception:
            return None

    @staticmethod
    def _normalize_rows(rows: Union[List[Sequence[Any]], List[dict]], headers: List[str]) -> List[List[Any]]:
        if not rows:
            return []
        if rows and not isinstance(rows[0], dict):
            out = []
            for r in rows:
                r = list(r)
                if len(r) < len(headers):
                    r = r + [""] * (len(headers) - len(r))
                out.append(r[: len(headers)])
            return out
        out = []
        for d in rows:
            out.append([d.get(h, "") for h in headers])
        return out

    @staticmethod
    def _find_code_column(headers: List[str]) -> int | None:
        for i, h in enumerate(headers):
            if str(h).lower() == "code":
                return i
        return None

    # models/logs_table_model.py (внутри класса LogsTableModel)

