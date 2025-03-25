"""
Crop region selection dialog window

Key Responsibilities:
- Provides UI for interactive video crop selection
- Coordinates between visual selection and numeric input controls
- Handles video resolution/viewport coordinate conversions

Main Components:
- CropSelectionWindow: QDialog containing:
  - Video preview viewport (GraphicsView)
  - SpinBox controls for precise crop coordinates
  - Slider for video timeline navigation

Dependencies:
- PySide6.QtWidgets: Dialog and input components
- .crop_selection_widgets: GraphicsView integration
- .ffmpeg_utils: Video resolution detection
- .ui.CropSelectionWindow: Generated UI layout
"""

from pathlib import Path

from PySide6 import QtCore, QtWidgets

from .crop_selection_widgets import RectangleGeometry
from .ffmpeg_utils import FFmpeg
from .ui.CropSelectionWindow import Ui_Dialog


class CropSelectionWindow(QtWidgets.QDialog, Ui_Dialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.horizontalSlider.sliderReleased.connect(self.slider_released)
        self.graphicsView.rectangle_changed.connect(self.update_spinboxes)
        self.spinBox_x.valueChanged.connect(self.update_rectangle)
        self.spinBox_y.valueChanged.connect(self.update_rectangle)
        self.spinBox_w.valueChanged.connect(self.update_rectangle)
        self.spinBox_h.valueChanged.connect(self.update_rectangle)
        self.spinboxes_signal_enabled = True

    def set_file(self, file: Path):
        self.graphicsView.set_file(file)
        self.video_resolution = FFmpeg().get_resolution(file)

    @QtCore.Slot(int)
    def update_rectangle(self, _):
        if not self.spinboxes_signal_enabled:
            return
        x, y = self.spinBox_x.value(), self.spinBox_y.value()
        w, h = self.spinBox_w.value(), self.spinBox_h.value()
        self.graphicsView.rectangle.setRect(x, y, w, h, move_points=True)

    @QtCore.Slot()
    def update_spinboxes(self):
        rect = self.graphicsView.rectangle.get_geometry()
        self.spinboxes_signal_enabled = False
        self.spinBox_x.setValue(rect.x)
        self.spinBox_y.setValue(rect.y)
        self.spinBox_w.setValue(rect.w)
        self.spinBox_h.setValue(rect.h)
        self.spinboxes_signal_enabled = True

    @QtCore.Slot(int)
    def slider_released(self):
        value = self.horizontalSlider.value()
        new_pos = int(self.graphicsView.player.duration() * value / 100)
        self.graphicsView.player.setPosition(new_pos)

    def show(self):
        super().show()
        w = self.graphicsView.width()
        h = self.graphicsView.height()
        self.spinBox_x.setMaximum(w)
        self.spinBox_y.setMaximum(h)
        self.spinBox_w.setMaximum(w)
        self.spinBox_h.setMaximum(h)
        self.graphicsView.init_selection_items(w=w, h=h)
        self.setMinimumSize(int(w * 1.1), int(h * 1.4))
        self.viewport_resolution = (w, h)
        self.update_spinboxes()

    def res_view2vid(self, w: int, h: int):
        new_w = int(w * self.video_resolution[0] / self.viewport_resolution[0])
        new_h = int(h * self.video_resolution[1] / self.viewport_resolution[1])
        return new_w, new_h

    def get_crop_rect(self):
        x, y = self.spinBox_x.value(), self.spinBox_y.value()
        w, h = self.spinBox_w.value(), self.spinBox_h.value()
        return RectangleGeometry(
            *self.res_view2vid(x, y), *self.res_view2vid(w, h)
        ).safe_bound(
            max_width=self.video_resolution[0], max_height=self.video_resolution[1]
        )
