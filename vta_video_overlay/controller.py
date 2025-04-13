from pathlib import Path

from loguru import logger as log
from PySide6 import QtCore, QtWidgets

from vta_video_overlay.crop_selection_widgets import RectangleGeometry
from vta_video_overlay.crop_selection_window import CropSelectionWindow
from vta_video_overlay.ffmpeg_utils import FFmpeg
from vta_video_overlay.pipeline import Pipeline
from vta_video_overlay.tda_file import Data


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
            path = pick_path_open(filter=self.tr("VPTAnalizer file(*.tda)"))
            if path == "":
                return
            self.pipeline.data = Data(path=Path(path), temp_enabled=temp_enabled)
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
        # self.pipeline.stage_progress.connect(self.stage_progress)
        # self.pipeline.stage_finished.connect(self.stage_finished)
        # self.pipeline.work_finished.connect(self.work_finished)
        self.pipeline.start()
