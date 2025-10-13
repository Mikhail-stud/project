# models/logs_table_model.py
from __future__ import annotations
from PyQt6.QtGui import QColor
from PyQt6.QtCore import (
    Qt,
    QAbstractTableModel,
    QModelIndex,
    QVariant,
)


class LogsTableModel(QAbstractTableModel):
    """
    Модель таблицы логов с чекбоксами в КАЖДОЙ ячейке.

    Основные моменты:
    - Чекбоксы реализованы через ItemIsUserCheckable + CheckStateRole в data/setData.
    - Стандартный делегат Qt сам рисует чекбокс + текст и меняет состояние по клику.
    - Никаких чекбоксов в заголовках: headerData возвращает только текст.
    - Есть удобные хелперы для сборки отмеченных значений.
    - Добавлены совместимые заглушки (checked_columns/rows и т.п.), чтобы ничего не сломалось,
      если где-то остались вызовы из старого кода.
    """

    def __init__(self, rows: list[list], headers: list[str], parent=None):
        super().__init__(parent)
        self._rows: list[list] = list(rows or [])
        self._headers: list[str] = list(headers or [])

        # матрица состояний чекбоксов для каждой ячейки
        r, c = self.rowCount(), self.columnCount()
        self._checked: list[list[bool]] = [[False for _ in range(c)] for __ in range(r)]
    
    def headers(self):
        """Совместимость со старым кодом: возврат списка заголовков как атрибут."""
        return list(self._headers)

    # ------------- базовый интерфейс модели -------------
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._headers)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                if 0 <= section < len(self._headers):
                    return self._headers[section]
                return ""
            else:
                # нумерация строк (по желанию)
                return str(section + 1)
        return None

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        r, c = index.row(), index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            # Текст рядом с чекбоксом
            try:
                return str(self._rows[r][c])
            except Exception:
                return ""

        if role == Qt.ItemDataRole.CheckStateRole:
            # Состояние чекбокса в ячейке
            return Qt.CheckState.Checked if self._checked[r][c] else Qt.CheckState.Unchecked

        if role == Qt.ItemDataRole.ForegroundRole:
            try:
                col_name = self._headers[c].lower()
            except Exception:
                col_name = ""
            if col_name == "code":
            # аккуратно парсим число
                val = str(self._rows[r][c]).strip()
                try:
                    code = int(val)
                except Exception:
                    code = None
                if code is not None:
                    if 200 <= code <= 299:
                        return QColor(0, 128, 0)   # зелёный
                    if 300 <= code <= 399:
                        return QColor(255, 165, 0)   # оранжевый
                    if 400 <= code <= 599:
                        return QColor(200, 0, 0)   # красный

        return None

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        # чекбокс в ячейке + обычная селекция
        return (Qt.ItemFlag.ItemIsEnabled |
                Qt.ItemFlag.ItemIsSelectable |
                Qt.ItemFlag.ItemIsUserCheckable)

    def setData(self, index: QModelIndex, value, role: int = Qt.ItemDataRole.EditRole) -> bool:
        if not index.isValid():
            return False

        if role == Qt.ItemDataRole.CheckStateRole:
            r, c = index.row(), index.column()
            try:
                state = Qt.CheckState(value)
            except Exception:
                state = Qt.CheckState.Unchecked

            new_val = (state == Qt.CheckState.Checked)
            if self._checked[r][c] != new_val:
                self._checked[r][c] = new_val
                self.dataChanged.emit(index, index, [Qt.ItemDataRole.CheckStateRole])
            return True

        return False

    # ------------- служебные методы -------------
    def set_rows(self, rows: list[list], headers: list[str] | None = None):
        """
        Полная замена данных модели (например, после загрузки/фильтрации).
        Корректно пересоздаёт матрицу чекбоксов нужного размера.
        """
        self.beginResetModel()
        self._rows = list(rows or [])
        if headers is not None:
            self._headers = list(headers or [])
        r, c = self.rowCount(), self.columnCount()
        self._checked = [[False for _ in range(c)] for __ in range(r)]
        self.endResetModel()

    def clear_checks(self):
        """Снять все отметки чекбоксов и обновить вид."""
        if not self._checked:
            return
        for r in range(len(self._checked)):
            for c in range(len(self._checked[r])):
                if self._checked[r][c]:
                    self._checked[r][c] = False
                    idx = self.index(r, c)
                    self.dataChanged.emit(idx, idx, [Qt.ItemDataRole.CheckStateRole])

    # ------------- хелперы для «Создать правило» -------------
    def get_checked_cells(self) -> list[tuple[int, int]]:
        """Список координат (row, col) всех отмеченных ячеек."""
        out = []
        for r, row in enumerate(self._checked):
            for c, v in enumerate(row):
                if v:
                    out.append((r, c))
        return out

    def get_checked_values(self) -> list:
        """Список значений (текстов) всех отмеченных ячеек."""
        out = []
        for r, c in self.get_checked_cells():
            try:
                out.append(self._rows[r][c])
            except Exception:
                pass
        return out

    def get_checked_values_by_column(self, col: int) -> list:
        """Список значений отмеченных ячеек только из колонки col."""
        out = []
        if not (0 <= col < self.columnCount()):
            return out
        for r in range(self.rowCount()):
            if self._checked[r][col]:
                out.append(self._rows[r][col])
        return out

    # ------------- сортировка (по тексту) -------------
    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder) -> None:
        """
        Простейшая сортировка по значению DisplayRole.
        Матрица чекбоксов переупорядочивается вместе со строками.
        """
        if not (0 <= column < self.columnCount()):
            return
        self.layoutAboutToBeChanged.emit()

        # подготавливаем пары (строка, чек-строка), чтобы сортировать синхронно
        paired = list(zip(self._rows, self._checked))
        reverse = (order == Qt.SortOrder.DescendingOrder)

        def key_func(pair):
            row, _chk = pair
            val = row[column] if 0 <= column < len(row) else ""
            return str(val).lower()

        paired.sort(key=key_func, reverse=reverse)

        # распаковываем обратно
        if paired:
            self._rows, self._checked = map(list, zip(*paired))
        else:
            self._rows, self._checked = [], []

        self.layoutChanged.emit()

    # ------------- совместимость со старым API (заглушки) -------------
    # Ниже методы, которые могли вызываться старым кодом, когда галки были в заголовках.
    # Теперь они просто вычисляются из текущей матрицы _checked, чтобы ничего не падало.

    def checked_columns(self) -> list[int]:
        """Список индексов колонок, где есть хотя бы одна отмеченная ячейка."""
        res = []
        for c in range(self.columnCount()):
            if any(self._checked[r][c] for r in range(self.rowCount())):
                res.append(c)
        return res

    def checked_rows(self) -> list[int]:
        """Список индексов строк, где есть хотя бы одна отмеченная ячейка."""
        res = []
        for r in range(self.rowCount()):
            if any(self._checked[r]):
                res.append(r)
        return res

    def is_column_checked(self, col: int) -> bool:
        """Считалось ранее как «галка в заголовке колонки». Теперь — есть ли отмеченные ячейки в колонке."""
        if not (0 <= col < self.columnCount()):
            return False
        return any(self._checked[r][col] for r in range(self.rowCount()))

    def is_row_checked(self, row: int) -> bool:
        """Считалось ранее как «галка в заголовке строки». Теперь — есть ли отмеченные ячейки в строке."""
        if not (0 <= row < self.rowCount()):
            return False
        return any(self._checked[row])

    # Управляющие методы «переключить галку в заголовке ...» больше не имеют смысла.
    # Оставим их как no-op, чтобы старые вызовы не падали.
    def toggle_column_checked(self, col: int):
        return

    def toggle_row_checked(self, row: int):
        return
