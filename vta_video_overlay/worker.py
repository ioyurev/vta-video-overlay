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
        tmpfile = Path(self.tempdir / "opencv_output.mp4")
        video_data = VideoData(video_path=self.video_file_path_input, data=self.data)

        cv = CVProcessor(
            video_data=video_data,
            path_output=tmpfile,
            plot_enabled=self.plot_enabled,
            crop_rect=self.crop_rect,
        )
        cv.progress_signal.connect(self.progress.emit)
        cv.run(start_timestamp=self.start_timestamp)
        progress = 50
        ff = FFmpeg()
        ff.signal.connect(self.progress.emit)
        ff.convert_video(
            path_input=tmpfile,
            path_output=self.video_file_path_output,
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
