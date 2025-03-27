import os
import shutil
import tempfile
import traceback
from pathlib import Path

from loguru import logger as log
from PySide6 import QtCore

from .crop_selection_widgets import RectangleGeometry
from .data_collections import ProcessProgress, ProcessResult
from .ffmpeg_utils import FFmpeg
from .opencv_processor import CVProcessor
from .tda_file import Data
from .video_data import VideoData


def clean(tempdir: str):
    log.info(QtCore.QCoreApplication.tr("Cleaning {tempdir}").format(tempdir=tempdir))
    if os.path.exists(tempdir):
        shutil.rmtree(tempdir)


class Pipeline(QtCore.QThread):
    stage_progress = QtCore.Signal(ProcessProgress)
    stage_finished = QtCore.Signal(tuple)
    work_finished = QtCore.Signal(ProcessResult)
    data: Data
    video_path_input: Path
    video_path_output: Path
    crop_rect: RectangleGeometry | None

    def run(self):
        try:
            self.execute()
            self.work_finished.emit(ProcessResult(is_success=True))
        except Exception:
            self.work_finished.emit(
                ProcessResult(is_success=False, traceback_msg=traceback.format_exc())
            )
        finally:
            clean(tempdir=self.tempdir)

    def execute(self):
        self.tempdir = Path(tempfile.mkdtemp())
        tmpfile1 = Path(self.tempdir / "out1.mp4")
        tmpfile2 = Path(self.tempdir / "out2.mp4")

        if FFmpeg().check_for_packets(video_path=self.video_path_input):
            file_to_overlay = self.video_path_input
            self.stage_progress.emit(ProcessProgress(value=100.0, frame=None))
        else:
            file_to_overlay = tmpfile1
            log.warning("Input video has no timestamps. Preconverting video...")
            FFmpeg().convert_video(
                path_input=self.video_path_input,
                path_output=file_to_overlay,
                signal=self.stage_progress,
            )

        video_data = VideoData(video_path=file_to_overlay, data=self.data)
        self.stage_finished.emit((len(video_data.timestamps) - 1, "2/3", "frame"))

        cv_agent = CVProcessor(
            video_data=video_data,
            path_output=tmpfile2,
            crop_rect=self.crop_rect,
        )
        cv_agent.progress_signal.connect(self.stage_progress.emit)
        cv_agent.run()
        self.stage_finished.emit((100.0, "3/3", "%"))

        FFmpeg().convert_video(
            path_input=tmpfile2,
            path_output=self.video_path_output,
            signal=self.stage_progress,
        )

    def set_metadata(
        self,
        op: str,
        samplename: str,
        coeff: list[str],
        temp_enabled: bool,
    ):
        self.data.operator = op
        self.data.sample = samplename
        self.data.temp_enabled = temp_enabled
        self.data.coeff = coeff
        self.data.recalc_temp()
