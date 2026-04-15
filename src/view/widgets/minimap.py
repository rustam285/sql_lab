from PySide6.QtWidgets import QGraphicsView
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QPen, QColor

class Minimap(QGraphicsView):
    def __init__(self, main_scene, parent=None):
        super().__init__(main_scene, parent)
        self.setRenderHints(QPainter.Antialiasing)
        self.setFixedWidth(200)
        self.setFixedHeight(150)
        self.setStyleSheet("background: rgba(30,30,30,0.8); border: 1px solid #555;")
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setInteractive(False)
        self.setDragMode(QGraphicsView.NoDrag)

        self._main_view = None
        self._viewport_rect = None

    def set_main_view(self, view):
        self._main_view = view
        if hasattr(view, 'viewportChanged'):
            view.viewportChanged.connect(self._update_viewport_rect)
        self._update_viewport_rect()

    def _update_viewport_rect(self):
        if not self._main_view or not self.scene():
            return

        root_rect = self.scene().sceneRect()
        if not root_rect.isValid() or root_rect.isNull():
            return

        self.setSceneRect(root_rect)
        self.fitInView(root_rect, Qt.KeepAspectRatio)

        visible_rect = self._main_view.mapToScene(self._main_view.viewport().rect()).boundingRect()
        top_left = self.mapFromScene(visible_rect.topLeft())
        bottom_right = self.mapFromScene(visible_rect.bottomRight())
        self._viewport_rect = QRectF(top_left, bottom_right).normalized()
        self.viewport().update()

    def drawForeground(self, painter, rect):
        super().drawForeground(painter, rect)
        if not self._viewport_rect:
            return

        painter.setPen(QPen(QColor(255, 165, 0), 2))
        painter.setBrush(QColor(255, 165, 0, 50))
        painter.drawRect(self._viewport_rect)

    def mousePressEvent(self, event):
        if self._main_view:
            scene_pos = self.mapToScene(event.pos())
            self._main_view.centerOn(scene_pos)
        event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self._main_view:
            scene_pos = self.mapToScene(event.pos())
            self._main_view.centerOn(scene_pos)
        event.accept()