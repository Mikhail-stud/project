from PyQt6.QtCore import QAbstractTableModel, Qt, QVariant
from PyQt6.QtGui import QColor


class LogsTableModel(QAbstractTableModel):
    """
    Модель данных для отображения логов в QTableView.
    Поддерживает сортировку и цветовую подсветку по HTTP-кодам.
    """

    def __init__(self, rows, headers, parent=None):
        super().__init__(parent)
        self._rows = rows
        self._headers = headers

    def rowCount(self, parent=None):
        return len(self._rows)

    def columnCount(self, parent=None):
        return len(self._headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return QVariant()

        value = self._rows[index.row()][index.column()]

        if role == Qt.ItemDataRole.DisplayRole:
            return str(value)

        # Цветовая подсветка HTTP-кодов
        if role == Qt.ItemDataRole.BackgroundRole and "code" in [h.lower() for h in self._headers]:
            try:
                code_index = [h.lower() for h in self._headers].index("code")
                if index.column() == code_index:
                    code = int(value)
                    if 200 <= code < 300:
                        return QColor("#ccffcc")  # зелёный для 2xx
                    elif 400 <= code < 600:
                        return QColor("#ffcccc")  # красный для 4xx/5xx
            except (ValueError, TypeError):
                pass

        return QVariant()

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return QVariant()

        if orientation == Qt.Orientation.Horizontal:
            return self._headers[section]
        else:
            return section + 1

    def sort(self, column, order):
        """Сортировка по столбцу."""
        self.layoutAboutToBeChanged.emit()
        try:
            self._rows.sort(
                key=lambda x: x[column] if x[column] is not None else "",
                reverse=order == Qt.SortOrder.DescendingOrder
            )
        except Exception:
            pass
        self.layoutChanged.emit()