import os
import shutil
import tempfile
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
    progress = QtCore.Signal(ProcessProgress)
    signal_finished = QtCore.Signal(ProcessResult)

    def __init__(
        self,
        parent,
        video_file_path_input: Path,
        video_file_path_output: Path,
        data: Data,
        start_timestamp: float,
        plot_enabled: bool,
        crop_rect: RectangleGeometry | None = None,
    ):
        super().__init__(parent=parent)
        self.video_file_path_input = video_file_path_input
        self.video_file_path_output = video_file_path_output
        self.data = data
        self.start_timestamp = start_timestamp
        self.plot_enabled = plot_enabled
        self.crop_rect = crop_rect

    def do_work(self):
        self.tempdir = Path(tempfile.mkdtemp())
        tmpfile1 = Path(self.tempdir / "out1.mp4")
        tmpfile2 = Path(self.tempdir / "out2.mp4")

        if FFmpeg().check_for_packets(video_path=self.video_file_path_input):
            file_to_overlay = self.video_file_path_input
            progress = 34
        else:
            file_to_overlay = tmpfile1
            log.warning("Input video has no timestamps. Preconverting video...")
            progress = FFmpeg().convert_video(
                path_input=self.video_file_path_input,
                path_output=file_to_overlay,
                signal=self.progress,
                current_progress=1,
            )

        video_data = VideoData(video_path=file_to_overlay, data=self.data)

        progress = CVProcessor(
            video_data=video_data,
            path_output=tmpfile2,
            progress_signal=self.progress,
            plot_enabled=self.plot_enabled,
            crop_rect=self.crop_rect,
        ).run(current_progress=progress, start_timestamp=self.start_timestamp)
        FFmpeg().convert_video(
            path_input=tmpfile2,
            path_output=self.video_file_path_output,
            signal=self.progress,
            current_progress=progress,
        )

    def run(self):
        # try:
        self.do_work()
        clean(tempdir=self.tempdir)
        self.signal_finished.emit(ProcessResult(is_success=True))
        # except Exception as e:
        # self.signal_finished.emit(ProcessResult(is_success=False, exception=e))
        # finally:
