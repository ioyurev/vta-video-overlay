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


class Worker(QtCore.QThread):
    stage_progress = QtCore.Signal(ProcessProgress)
    stage_finished = QtCore.Signal(tuple)
    work_finished = QtCore.Signal(ProcessResult)

    def __init__(
        self,
        video_file_path_input: Path,
        video_file_path_output: Path,
        data: Data,
        start_timestamp=0.0,
        parent=None,
        crop_rect: RectangleGeometry | None = None,
    ):
        super().__init__(parent=parent)
        self.video_file_path_input = video_file_path_input
        self.video_file_path_output = video_file_path_output
        self.data = data
        self.start_timestamp = start_timestamp
        self.crop_rect = crop_rect

    def do_work(self):
        self.tempdir = Path(tempfile.mkdtemp())
        tmpfile1 = Path(self.tempdir / "out1.mp4")
        tmpfile2 = Path(self.tempdir / "out2.mp4")

        if FFmpeg().check_for_packets(video_path=self.video_file_path_input):
            file_to_overlay = self.video_file_path_input
            self.stage_progress.emit(ProcessProgress(value=100.0, frame=None))
        else:
            file_to_overlay = tmpfile1
            log.warning("Input video has no timestamps. Preconverting video...")
            FFmpeg().convert_video(
                path_input=self.video_file_path_input,
                path_output=file_to_overlay,
                signal=self.stage_progress,
            )

        video_data = VideoData(video_path=file_to_overlay, data=self.data)
        self.stage_finished.emit((len(video_data.timestamps) - 1, "2/3", "frame"))

        CVProcessor(
            video_data=video_data,
            path_output=tmpfile2,
            progress_signal=self.stage_progress,
            crop_rect=self.crop_rect,
        ).run(start_timestamp=self.start_timestamp)
        self.stage_finished.emit((100.0, "3/3", "%"))

        FFmpeg().convert_video(
            path_input=tmpfile2,
            path_output=self.video_file_path_output,
            signal=self.stage_progress,
        )

    def run(self):
        try:
            self.do_work()
            self.work_finished.emit(ProcessResult(is_success=True))
        except Exception:
            self.work_finished.emit(
                ProcessResult(is_success=False, traceback_msg=traceback.format_exc())
            )
        finally:
            clean(tempdir=self.tempdir)
