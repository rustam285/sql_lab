from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QPen, QColor, QPainter

class DiagramScene(QGraphicsScene):
    tableMoved = Signal(str, float, float)
    positionMoveFinished = Signal(str, float, float, float, float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBackgroundBrush(QColor(245, 245, 245))
        self.setSceneRect(-3000, -3000, 6000, 6000)
        self._items_map = {}
        self.edges = []  # Храним связи для перерисовки
        self.grid_visible = True

    def clear(self):
        super().clear()
        self._items_map.clear()
        self.edges.clear()

    def toggle_grid(self, state):
        self.grid_visible = state
        self.update()  # Перерисовка фона

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        if not self.grid_visible:
            return
            
        grid_size = 20
        painter.setPen(QPen(QColor(210, 210, 210), 1, Qt.DotLine))
        
        left = int(rect.left()) - (int(rect.left()) % grid_size)
        top = int(rect.top()) - (int(rect.top()) % grid_size)
        
        for x in range(left, int(rect.right()), grid_size):
            painter.drawLine(x, rect.top(), x, rect.bottom())
        for y in range(top, int(rect.bottom()), grid_size):
            painter.drawLine(rect.left(), y, rect.right(), y)

    def add_table(self, table) -> 'TableItem':
        from .items.table_item import TableItem
        item = TableItem(table)
        item.positionChanged.connect(self._on_table_moved)
        item.positionMoveFinished.connect(self.positionMoveFinished)
        self.addItem(item)
        self._items_map[table.id] = item
        return item

    def add_edge(self, edge):
        self.edges.append(edge)
        self.addItem(edge)

    def get_item(self, table_id):
        return self._items_map.get(table_id)

    def _on_table_moved(self, table_id, x, y):
        self.tableMoved.emit(table_id, x, y)
        # Пересчитываем пути всех связей при движении
        for edge in self.edges:
            edge.rebuild_path()