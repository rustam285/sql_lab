import math
from PySide6.QtWidgets import QGraphicsPathItem
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPainterPath, QPen, QBrush, QColor, QPainter, QPolygonF
from src.model.entities import Relationship
from src.utils.routing_engine import OrthogonalRouter

class EdgeItem(QGraphicsPathItem):
    GRID_SIZE = 20

    def __init__(self, relationship: Relationship, src_table_item, dst_table_item):
        super().__init__()
        self.relationship = relationship
        self.src_table = src_table_item
        self.dst_table = dst_table_item
        
        self.setZValue(0)
        self.setPen(QPen(QColor(80, 80, 80), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        self.setCacheMode(QGraphicsPathItem.NoCache) # Отключаем кэш для мгновенной перерисовки
        self.setPath(QPainterPath()) # Инициализация пустым путем
        self.rebuild_path()

    def boundingRect(self) -> QRectF:
        path_rect = self.path().boundingRect()
        if path_rect.isEmpty():
            return QRectF(0, 0, 20, 20)
        # Запас под наконечник, чтобы не обрезался при зуме/движении
        return path_rect.adjusted(-15, -15, 15, 15)

    def rebuild_path(self):
        # 1. Сообщаем сцене, что геометрия МЕНЯЕТСЯ (до изменения пути!)
        self.prepareGeometryChange()
        
        start_point = self._get_anchor_point(self.src_table, self.dst_table, self.relationship.src_col)
        end_point = self._get_anchor_point(self.dst_table, self.src_table, self.relationship.dst_col)

        obstacles = []
        scene = self.src_table.scene()
        if scene:
            for item in scene.items():
                if isinstance(item, EdgeItem): continue
                if item != self.src_table and item != self.dst_table:
                    obstacles.append(item.mapRectToScene(item.boundingRect()))

        router = OrthogonalRouter(self.GRID_SIZE)
        points = router.route(start_point, end_point, obstacles)

        new_path = QPainterPath()
        if points:
            new_path.moveTo(points[0])
            for pt in points[1:]:
                new_path.lineTo(pt)

        # 2. Применяем новый путь
        self.setPath(new_path)
        
        # 3. Форсируем перерисовку элемента и области сцены
        self.update()
        if self.scene():
            self.scene().update(self.boundingRect().adjusted(-20, -20, 20, 20))

    def _get_anchor_point(self, my_table, other_table, col_name):
        rect = my_table.mapRectToScene(my_table.boundingRect())
        idx = my_table.table.get_column_index(col_name)
        if idx is None: idx = 0
        
        y_offset = my_table.HEADER_HEIGHT + my_table.PADDING + (idx * my_table.ROW_HEIGHT) + (my_table.ROW_HEIGHT / 2)
        center_x = rect.center().x()
        other_center_x = other_table.mapRectToScene(other_table.boundingRect()).center().x()
        local_x = rect.width() if other_center_x > center_x else 0
        
        return my_table.mapToScene(QPointF(local_x, y_offset))

    def paint(self, painter, option, widget=None):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        # Базовая линия
        super().paint(painter, option, widget)

        # Наконечник
        path = self.path()
        if path.isEmpty():
            painter.restore()
            return

        # Безопасное извлечение точек (Qt6 совместимо)
        elements = [QPointF(path.elementAt(i).x, path.elementAt(i).y) for i in range(path.elementCount())]
        if len(elements) < 2:
            painter.restore()
            return

        p_end = elements[-1]
        p_prev = elements[-2]
        angle = math.atan2(p_end.y() - p_prev.y(), p_end.x() - p_prev.x())
        size = 12.0

        color = QColor(0, 120, 215) if self.isSelected() else QColor(80, 80, 80)
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)

        arrow = QPolygonF()
        arrow.append(p_end)
        arrow.append(QPointF(p_end.x() - size * math.cos(angle - math.pi / 6),
                             p_end.y() - size * math.sin(angle - math.pi / 6)))
        arrow.append(QPointF(p_end.x() - size * math.cos(angle + math.pi / 6),
                             p_end.y() - size * math.sin(angle + math.pi / 6)))
        painter.drawPolygon(arrow)
        painter.restore()