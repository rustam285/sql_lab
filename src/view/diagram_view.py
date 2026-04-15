from PySide6.QtWidgets import QGraphicsView
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QWheelEvent, QPainter

class DiagramView(QGraphicsView):
    viewportChanged = Signal()
    ZOOM_FACTOR = 1.15

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() & Qt.ControlModifier:
            factor = self.ZOOM_FACTOR if event.angleDelta().y() > 0 else 1 / self.ZOOM_FACTOR
            self.scale(factor, factor)
            self.viewportChanged.emit()
        else:
            super().wheelEvent(event)

    def scrollContentsBy(self, dx: int, dy: int):
        super().scrollContentsBy(dx, dy)
        self.viewportChanged.emit()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.viewportChanged.emit()

    def fit_to_view(self):
        rect = self.scene().itemsBoundingRect()
        if rect.isNull():
            return
        self.fitInView(rect.adjusted(-50, -50, 50, 50), Qt.KeepAspectRatio)
        self.viewportChanged.emit()