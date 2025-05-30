"""
Central controller for application logic and component coordination

Key Responsibilities:
- Manages file selection dialogs for sensor data (.tda) and video files
- Coordinates video cropping operations through CropSelectionWindow
- Controls main video processing pipeline execution
- Handles inter-component communication via Qt signals/slots
- Bridges UI interactions with backend processing logic

Core Functionality:
- Validates and loads sensor data files
- Initializes video processing parameters
- Manages temporary directories and cleanup
- Handles error states and user notifications
- Maintains application state during processing
"""

from pathlib import Path

from loguru import logger as log
from PySide6 import QtCore, QtWidgets

from vta_video_overlay.crop_selection_widgets import RectangleGeometry
from vta_video_overlay.crop_selection_window import CropSelectionWindow
from vta_video_overlay.data_file import Data
from vta_video_overlay.ffmpeg_utils import FFmpeg
from vta_video_overlay.pipeline import Pipeline


def pick_path_save() -> str:
    return QtWidgets.QFileDialog.getSaveFileName(
        filter=QtCore.QCoreApplication.tr("Video(*.mp4)")
    )[0]


def pick_path_open(filter=QtCore.QCoreApplication.tr("All files(*.*)")):
    return QtWidgets.QFileDialog.getOpenFileName(filter=filter)[0]


class Controller(QtCore.QObject):
    pipeline = Pipeline()
    crop_done = QtCore.Signal(RectangleGeometry)

    @QtCore.Slot()
    def crop(self):
        if self.pipeline.video_path_input == "":
            return
        self.sel_win = CropSelectionWindow(parent=self.parent())
        self.sel_win.accepted.connect(self.crop_done_slot)
        self.sel_win.set_file(file=Path(self.pipeline.video_path_input))
        self.sel_win.show()

    def crop_done_slot(self):
        crop_rect = self.sel_win.get_crop_rect()
        self.pipeline.crop_rect = crop_rect
        self.crop_done.emit(crop_rect)

    @QtCore.Slot()
    def pick_tda(self, temp_enabled: bool):
        try:
            file_filter = self.tr("Data files (*.tda *.vtaz)")
            path = pick_path_open(filter=file_filter)
            if path == "":
                return
            path = Path(path)
            if path.suffix.lower() == ".tda":
                self.pipeline.data = Data.from_tda_file(
                    path=path, temp_enabled=temp_enabled
                )
            elif path.suffix.lower() == ".vtaz":
                self.pipeline.data = Data.from_vtaz_file(
                    path=path, temp_enabled=temp_enabled
                )
            return self.pipeline.data
        except Exception as e:
            log.error(
                self.tr(
                    "TDA file load failed | Path: {} | Temp Enabled: {} | Error: {}"
                ),
                path,
                temp_enabled,
                e,
            )
            QtWidgets.QMessageBox.critical(
                self,
                "Error",
                self.tr("Failed to read TDA file."),
            )

    @QtCore.Slot()
    def pick_video(self):
        path = pick_path_open(filter=self.tr("Video(*.asf *.mp4);;All files(*.*)"))
        if path == "":
            return
        try:
            size = FFmpeg().get_resolution(video_path=path)
            self.pipeline.video_path_input = Path(path)
            return path, size
        except Exception as e:
            log.error(self.tr("Video file load failed | Path: {} | Error: {}"), path, e)
            QtWidgets.QMessageBox.critical(
                self,
                "Error",
                self.tr("Failed to read video file."),
            )

    @QtCore.Slot()
    def overlay(self, convert_excel: bool = True):
        path_str = pick_path_save()
        if path_str == "":
            return
        savepath = Path(path_str)

        log.info(
            self.tr("Operator: {operator}").format(operator=self.pipeline.data.operator)
        )
        log.info(self.tr("Sample: {sample}").format(sample=self.pipeline.data.sample))
        log.info(
            self.tr("Temperature calibration enabled: {bool}").format(
                bool=self.pipeline.data.temp_enabled
            )
        )
        log.info(
            self.tr("Polynomial coefficients: {coeff}").format(
                coeff=self.pipeline.data.coeff
            )
        )
        self.pipeline.video_path_output = savepath
        if convert_excel:
            excelpath = Path(self.pipeline.data.path).with_suffix(".xlsx")
            self.pipeline.data.to_excel(excelpath)
        self.pipeline.start()
