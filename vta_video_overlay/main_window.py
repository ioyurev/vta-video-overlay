"""
Main application window and central UI controller

Key Responsibilities:
- Serves as primary user interface for video overlay operations
- Coordinates data flow between UI components and processing backend
- Manages application state and persistent configurations
- Handles system tray integration and background operations

Usage Flow:
1. File selection (.tda + video)
2. Parameter configuration
3. Optional crop selection
4. Processing initialization
5. Real-time progress monitoring
6. Completion notification/error handling

Preview System:
- OpenCV-to-Qt image conversion pipeline
- Aspect ratio-preserving scaling
- Frame buffer management
- Low-latency preview updates
"""

import platform
import subprocess
from pathlib import Path

from loguru import logger as log
from PySide6 import QtCore, QtGui, QtWidgets

from vta_video_overlay.__version__ import __version__
from vta_video_overlay.about_window import AboutWindow
from vta_video_overlay.config import appdata_path
from vta_video_overlay.controller import Controller
from vta_video_overlay.crop_selection_widgets import RectangleGeometry
from vta_video_overlay.data_collections import ProcessProgress, ProcessResult
from vta_video_overlay.data_file import Data
from vta_video_overlay.file_widget_base import FileDataWidgetBase
from vta_video_overlay.ui.MainWindow import Ui_MainWindow


def open_file_explorer(path: Path):
    system = platform.system()
    if system == "Windows":
        subprocess.Popen(["explorer", path], shell=True)
    elif system == "Linux":
        subprocess.Popen(["xdg-open", path])
    else:
        print("Unsupported operating system")


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, controller: Controller):
        super().__init__()
        self.setupUi(self)

        self.controller = controller
        self.controller.setParent(self)
        self.controller.crop_done.connect(self.crop_done)

        self.btn_tda.clicked.connect(self.pick_file)
        self.btn_video.clicked.connect(self.pick_video)
        self.btn_convert.clicked.connect(self.overlay)
        self.statusbar.addWidget(
            QtWidgets.QLabel(self.tr("Version: {v}").format(v=__version__))
        )
        self.about_window = AboutWindow(parent=self)
        self.actionAbout = QtGui.QAction(self.tr("About"), self)
        self.actionAbout.triggered.connect(self.show_about)
        self.menubar.addAction(self.actionAbout)

        self.explorer_action = QtGui.QAction(self.tr("Open config folder"), self)
        self.explorer_action.triggered.connect(lambda: open_file_explorer(appdata_path))
        self.menubar.addAction(self.explorer_action)

        self.crop_action = QtGui.QAction(self.tr("Crop"), self)
        self.crop_action.triggered.connect(self.controller.crop)
        self.crop_action.setEnabled(False)
        self.menubar.addAction(self.crop_action)

        self.video_preview.setScaledContents(True)

    def overlay(self):
        self.set_stuff_enabled(False)
        convert_excel = self.cb_excel.isChecked()
        self.controller.pipeline.stage_progress.connect(self.update_progressbar)
        self.controller.pipeline.stage_finished.connect(self.stage_finished)
        self.controller.pipeline.work_finished.disconnect()
        self.controller.pipeline.work_finished.connect(self.finished)
        log.info(self.tr("Started video processing"))
        self.controller.overlay(convert_excel=convert_excel)

    # @QtCore.Slot()
    def crop_done(self, rect: RectangleGeometry):
        log.info(self.tr("Crop done: {xywh}").format(xywh=rect))
        w = rect.w * self.video_preview.height() // rect.h
        self.video_preview.setMinimumWidth(w)

    @QtCore.Slot()
    def pick_file(self):
        result = self.controller.pick_file()
        if result is not None:
            data, widget = result
            log.info(self.tr("Selected tda file: {path}").format(path=data.path))
            self.data_to_gui(data=data, widget=widget)

    @QtCore.Slot()
    def pick_video(self):
        path, size = self.controller.pick_video()
        log.info(self.tr("Selected video: {path}").format(path=path))
        self.edit_video.setText(path)
        self.crop_action.setEnabled(True)
        self.video_preview.setMinimumHeight(self.video_preview.height())
        self.video_preview.setMinimumWidth(
            int(size[0] * self.video_preview.height() / size[1])
        )

    @QtCore.Slot()
    def show_about(self):
        self.about_window.show()
        self.about_window.raise_()

    def set_stuff_enabled(self, val: bool):
        self.btn_tda.setEnabled(val)
        self.btn_video.setEnabled(val)
        self.btn_convert.setEnabled(val)
        self.edit_tda.setEnabled(val)
        self.edit_video.setEnabled(val)
        self.cb_excel.setEnabled(val)

    def data_to_gui(self, data: Data, widget: FileDataWidgetBase):
        self.edit_tda.setText(str(data.path))

        # Ensure widget_container has a layout
        container_layout = self.widget_container.layout()
        if container_layout is None:
            container_layout = QtWidgets.QVBoxLayout(self.widget_container)
            container_layout.setContentsMargins(0, 0, 0, 0)
        else:
            # Clear previous widgets from layout
            while container_layout.count():
                child = container_layout.takeAt(0)
                if child and child.widget():
                    child.widget().deleteLater()

        # Add new widget if provided
        if widget:
            container_layout.addWidget(widget)

    # @QtCore.Slot(ProcessResult)
    def finished(self, tpl: ProcessResult):
        self.raise_()
        if tpl.is_success:
            QtWidgets.QMessageBox.information(
                self, "VTA video overlay", self.tr("Video processing completed")
            )  # type: ignore
        else:
            log.error(tpl.traceback_msg)
            QtWidgets.QMessageBox.critical(
                self,
                self.tr("Error"),
                self.tr(
                    f"Video processing failed.\nException occurred.\n\n{tpl.traceback_msg}"
                ),
            )
        self.set_stuff_enabled(True)
        self.progressbar.setValue(0)

    # @QtCore.Slot(ProcessProgress)
    def update_progressbar(self, progress: ProcessProgress):
        if progress.frame is not None:
            try:
                self.video_preview.setPixmap(progress.frame.to_pixmap())
            except Exception as e:
                log.exception(e)
        self.progressbar.setValue(progress.value)

    def stage_finished(self, tpl):
        total, stage_str, unit = tpl
        self.progressbar.setValue(0)
        self.progressbar.setMaximum(total)
