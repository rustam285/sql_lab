from PySide6.QtWidgets import QGraphicsObject, QGraphicsItem
from PySide6.QtCore import Qt, QRectF, QPointF, Signal
from PySide6.QtGui import QPainter, QPen, QBrush, QFont, QPainterPath, QColor
from src.model.entities import Table

class TableItem(QGraphicsObject):
    positionChanged = Signal(str, float, float)
    positionMoveFinished = Signal(str, float, float, float, float)

    GRID_SIZE = 20
    HEADER_HEIGHT = 30
    ROW_HEIGHT = 22
    PADDING = 10
    CORNER_RADIUS = 8

    def __init__(self, table: Table, parent=None):
        super().__init__(parent)
        self.table = table
        self._drag_start_pos = QPointF(table.x, table.y)
        self.setFlags(QGraphicsObject.ItemIsMovable | 
                      QGraphicsObject.ItemIsSelectable | 
                      QGraphicsObject.ItemSendsGeometryChanges)
        self.setCacheMode(QGraphicsObject.DeviceCoordinateCache)
        self.setPos(table.x, table.y)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            self.table.x = self.x()
            self.table.y = self.y()
            self.positionChanged.emit(self.table.id, self.x(), self.y())
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        self._drag_start_pos = self.pos()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self.pos() != self._drag_start_pos:
            old_pos = self._drag_start_pos
            new_pos = self.pos()
            self.positionMoveFinished.emit(
                self.table.id,
                old_pos.x(), old_pos.y(),
                new_pos.x(), new_pos.y()
            )

    def boundingRect(self) -> QRectF:
        if not self.table.columns:
            return QRectF(0, 0, 180, self.HEADER_HEIGHT + self.PADDING)
        
        index_texts = [f"UNI{ 'QUE' if idx.is_unique else 'NDX'} {idx.name} ({', '.join(idx.columns)})" for idx in self.table.indexes]
        check_texts = [f"CHECK {check}" for check in self.table.checks]

        max_column_width = max(len(c.name) + len(c.type) + 5 for c in self.table.columns)
        max_index_width = max((len(text) for text in index_texts), default=0)
        max_check_width = max((len(text) for text in check_texts), default=0)
        max_w = max(max_column_width, max_index_width, max_check_width)

        width = max(180, max_w * 7 + self.PADDING * 2)
        height = self.HEADER_HEIGHT + (len(self.table.columns) + len(index_texts) + len(check_texts)) * self.ROW_HEIGHT + self.PADDING
        return QRectF(0, 0, width, height)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.boundingRect()

        # 1. Фон карточки
        bg_color = QColor(255, 255, 255) if not self.table.is_view else QColor(240, 248, 255)
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(QColor(120, 120, 120), 1))
        painter.drawRoundedRect(rect, self.CORNER_RADIUS, self.CORNER_RADIUS)

        # 2. Заголовок (рисуем отдельным путем, чтобы скруглить только верх)
        header_rect = QRectF(0, 0, rect.width(), self.HEADER_HEIGHT)
        header_color = QColor(45, 45, 45) if not self.table.is_view else QColor(0, 110, 150)
        painter.setBrush(QBrush(header_color))
        painter.setPen(Qt.NoPen)
        
        path = QPainterPath()
        path.moveTo(self.CORNER_RADIUS, 0)
        path.arcTo(0, 0, self.CORNER_RADIUS * 2, self.CORNER_RADIUS * 2, 90, 90)
        path.lineTo(0, self.HEADER_HEIGHT)
        path.lineTo(rect.width(), self.HEADER_HEIGHT)
        path.arcTo(rect.width() - self.CORNER_RADIUS * 2, 0, self.CORNER_RADIUS * 2, self.CORNER_RADIUS * 2, 0, 90)
        path.closeSubpath()
        painter.drawPath(path)

        # 3. Имя таблицы (явно задаем перо и шрифт)
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        painter.drawText(header_rect, Qt.AlignCenter, self.table.name or "Table")

        # 4. Колонки
        painter.setPen(QColor(30, 30, 30))
        y_offset = self.HEADER_HEIGHT + self.PADDING
        
        for col in self.table.columns:
            icon = "🔑 " if col.is_pk else ""
            is_fk = "_id" in col.name.lower() or col.name.lower().endswith("_id")
            
            font = QFont("Consolas", 9)
            if col.is_pk: font.setBold(True)
            if is_fk: font.setItalic(True)
            painter.setFont(font)
            
            painter.drawText(self.PADDING, y_offset, f"{icon}{col.name} ({col.type})")
            y_offset += self.ROW_HEIGHT

        if self.table.indexes:
            painter.setPen(QColor(80, 80, 80))
            painter.setFont(QFont("Consolas", 8, QFont.Bold))
            painter.drawText(self.PADDING, y_offset, "Indexes:")
            y_offset += self.ROW_HEIGHT
            painter.setFont(QFont("Consolas", 8))
            for idx in self.table.indexes:
                prefix = "UNIQUE " if idx.is_unique else "INDEX "
                painter.drawText(self.PADDING, y_offset, f"{prefix}{idx.name}: {', '.join(idx.columns)}")
                y_offset += self.ROW_HEIGHT

        if self.table.checks:
            painter.setPen(QColor(120, 60, 60))
            painter.setFont(QFont("Consolas", 8, QFont.StyleItalic))
            painter.drawText(self.PADDING, y_offset, "Checks:")
            y_offset += self.ROW_HEIGHT
            for check in self.table.checks:
                painter.drawText(self.PADDING, y_offset, check)
                y_offset += self.ROW_HEIGHT