from PyQt6.QtWidgets import QHeaderView, QStyleOptionButton, QStyle
from PyQt6.QtCore import Qt, QRect, QPoint
from PyQt6.QtGui import QPainter



class CheckableHeaderView(QHeaderView):
    """
    Надежный заголовок с чекбоксами в каждой секции.
    Работает и для горизонтального, и для вертикального заголовка.
    """

    _MARGIN = 6

    def __init__(self, orientation: Qt.Orientation, parent=None):
        super().__init__(orientation, parent)
        self.setSectionsClickable(True)

    def _section_rect(self, section: int) -> QRect:
        """
        Возвращает QRect полной секции (в координатах заголовка).
        Использует sectionPosition и sectionSize (PyQt6).
        """
        if self.orientation() == Qt.Orientation.Horizontal:
            x = self.sectionPosition(section)
            w = self.sectionSize(section)
            return QRect(x, 0, w, self.height())
        else:
            y = self.sectionPosition(section)
            h = self.sectionSize(section)
            return QRect(0, y, self.width(), h)

    def _checkbox_rect(self, section: int) -> QRect:
        """
        Вычисляет rect для чекбокса внутри секции (с отступом _MARGIN).
        """
        sec_rect = self._section_rect(section)

        # Подготовим опцию для получения размера индикатора через стиль
        opt = QStyleOptionButton()
        opt.state = QStyle.StateFlag.State_Enabled

        # Получаем размер индикатора (корректно — с валидной опцией и self)
        indicator_rect = self.style().subElementRect(QStyle.SubElement.SE_CheckBoxIndicator, opt, self)

        # Позиционируем чекбокс: слева с небольшим отступом, центр по вертикали секции
        if self.orientation() == Qt.Orientation.Horizontal:
            x = sec_rect.left() + self._MARGIN
            y = sec_rect.top() + (sec_rect.height() - indicator_rect.height()) // 2
            return QRect(x, y, indicator_rect.width(), indicator_rect.height())
        else:
            x = sec_rect.left() + (sec_rect.width() - indicator_rect.width()) // 2
            y = sec_rect.top() + self._MARGIN
            return QRect(x, y, indicator_rect.width(), indicator_rect.height())

    def paintSection(self, painter: QPainter, rect: QRect, logicalIndex: int):
        # Сначала стандартная отрисовка заголовка (фон и текст)
        print("paintSection called for logicalIndex:", logicalIndex)
        super().paintSection(painter, rect, logicalIndex)
        painter.save()
        painter.fillRect(rect, Qt.GlobalColor.yellow)
        painter.restore()

        model = self.model()
        if model is None:
            return

        # Берём состояние чекбокса через модель (CheckStateRole)
        state = model.headerData(logicalIndex, self.orientation(), Qt.ItemDataRole.CheckStateRole)
        if state is None:
            return

        # Рисуем чекбокс
        print("paintSection idx", logicalIndex, "rect", rect)
        sec_rect = rect
        indicator_size = self.style().subElementRect(QStyle.SubElement.SE_CheckBoxIndicator, QStyleOptionButton(), self).size()
        x = sec_rect.left() + self._MARGIN
        y = sec_rect.top() + (sec_rect.height() - indicator_size.height()) // 2
        cb_rect = QRect(x,y, indicator_size.width(), indicator_size.height())
        #cb_rect = self._checkbox_rect(logicalIndex)
        print("-> checkbox rect", cb_rect)
        opt = QStyleOptionButton()
        opt.rect = cb_rect
        opt.state = QStyle.StateFlag.State_Enabled
        if state == Qt.CheckState.Checked:
            opt.state |= QStyle.StateFlag.State_On
        else:
            opt.state |= QStyle.StateFlag.State_Off

        # drawControl с CE_CheckBox безопасен и переносим отрисовку на стиль
        self.style().drawControl(QStyle.ControlElement.CE_CheckBox, opt, painter, self)

    def mousePressEvent(self, event):
        pos = event.pos()
        idx = self.logicalIndexAt(pos)
        if idx < 0:
            return super().mousePressEvent(event)

        model = self.model()
        if model is None:
            return super().mousePressEvent(event)

        # Если клик попал в область чекбокса — переключим состояние через модель
        if self._checkbox_rect(idx).contains(pos):
            cur = model.headerData(idx, self.orientation(), Qt.ItemDataRole.CheckStateRole)
            new_state = Qt.CheckState.Unchecked if cur == Qt.CheckState.Checked else Qt.CheckState.Checked
            # Устанавливаем через стандартный setHeaderData (модель должна это поддерживать)
            model.setHeaderData(idx, self.orientation(), new_state, Qt.ItemDataRole.CheckStateRole)
            # Не передаём событие дальше — чтобы не запускать сортировку/другое поведение
            return

        return super().mousePressEvent(event)




