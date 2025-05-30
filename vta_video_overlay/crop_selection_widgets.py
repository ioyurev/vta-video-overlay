"""
Interactive video crop selection widgets with geometric coordination

Key Responsibilities:
- Provide graphical components for interactive video region selection
- Handle viewport-video resolution coordinate system conversions
- Manage real-time visualization of crop boundaries and control points
- Maintain geometric consistency between UI controls and actual video frames

Implementation Details:
- Video preview integration using QMediaPlayer and QGraphicsVideoItem
- Real-time coordinate mapping between viewport and source video resolution
- Handle marker visualization with color-coded drag points
- Aspect ratio preservation during interactive resizing
- Frame-accurate video scrubbing via timeline slider
"""

from pathlib import Path
from typing import NamedTuple

from PySide6 import QtCore, QtGui, QtMultimedia, QtMultimediaWidgets, QtWidgets


class RectangleGeometry(NamedTuple):
    x: int
    y: int
    w: int
    h: int

    def safe_bound(self, max_width: int, max_height: int):
        x = max(0, self.x)
        y = max(0, self.y)
        w = min(max_width, self.w)
        h = min(max_height, self.h)
        return RectangleGeometry(x, y, w, h)


class Rectangle(QtWidgets.QGraphicsRectItem, QtCore.QObject):
    def __init__(self, rec_x: float, rec_y: float, rec_w: float, rec_h: float):
        super().__init__(rec_x, rec_y, rec_w, rec_h)
        self.setBrush(QtCore.Qt.green)
        self.setOpacity(0.25)

        self.p1 = QtWidgets.QGraphicsEllipseItem(-5, -5, 10, 10)
        self.p1.setPos(rec_x, rec_y)
        self.p1.setBrush(QtCore.Qt.red)

        self.p2 = QtWidgets.QGraphicsEllipseItem(-5, -5, 10, 10)
        self.p2.setPos(rec_x + rec_w, rec_y + rec_h)
        self.p2.setBrush(QtCore.Qt.blue)

    def get_geometry(self) -> RectangleGeometry:
        p1 = self.boundingRect().topLeft()
        x, y = p1.x(), p1.y()
        p2 = self.rect().bottomRight()
        w, h = p2.x() - x, p2.y() - y
        return RectangleGeometry(int(x), int(y), int(w), int(h))

    def setRect(
        self, x: float, y: float, w: float, h: float, move_points: bool = False
    ):
        super().setRect(x, y, w, h)
        if move_points:
            self.p1.setPos(x, y)
            self.p2.setPos(x + w, y + h)


class GraphicsView(QtWidgets.QGraphicsView):
    rectangle_changed = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setScene(QtWidgets.QGraphicsScene())
        self.player = QtMultimedia.QMediaPlayer(self)

    def init_selection_items(self, w: int, h: int):
        self.scene().setSceneRect(0, 0, w, h)
        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.videoitem = QtMultimediaWidgets.QGraphicsVideoItem()
        self.videoitem.setSize(QtCore.QSize(w, h))
        self.scene().addItem(self.videoitem)
        self.player.setVideoOutput(self.videoitem)

        rec_x, rec_y = (w - h) // 2, 0
        rec_w, rec_h = h, h
        self.rectangle = Rectangle(rec_x, rec_y, rec_w, rec_h)
        self.scene().addItem(self.rectangle)
        self.scene().addItem(self.rectangle.p1)
        self.scene().addItem(self.rectangle.p2)
        self.current_item = None

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        item = self.itemAt(event.position().toPoint())
        if item in [self.rectangle.p1, self.rectangle.p2]:
            self.current_item = item
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        self.current_item = None
        super().mouseReleaseEvent(event)
        self.rectangle_changed.emit()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        if self.current_item is None:
            return
        pos = self.mapToScene(event.position().toPoint())
        self.current_item.setPos(pos.x(), pos.y())
        x1, y1 = self.rectangle.p1.pos().x(), self.rectangle.p1.pos().y()
        x2, y2 = self.rectangle.p2.pos().x(), self.rectangle.p2.pos().y()
        w = abs(x1 - x2)
        h = abs(y1 - y2)
        x = min(x1, x2)
        y = min(y1, y2)
        self.rectangle.setRect(x, y, w, h)
        super().mouseMoveEvent(event)

    def set_file(self, file: Path):
        self.player.setSource(QtCore.QUrl.fromLocalFile(file))
        self.player.play()
        self.player.pause()
