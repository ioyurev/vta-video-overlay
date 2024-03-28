from .tda_file import Data
from .opencv_processor import CVProcessor
from .ffmpeg_utils import FFmpeg
from .video_data import VideoData
from .data_collections import ProcessProgress, ProcessResult
from pathlib import Path
from PySide6 import QtCore
import tempfile
import shutil
import os


def clean(tempdir: str):
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
    ):
        super().__init__(parent=parent)
        self.video_file_path_input = video_file_path_input
        self.video_file_path_output = video_file_path_output
        self.data = data
        self.start_timestamp = start_timestamp
        self.tempdir = Path(tempfile.mkdtemp())
        self.tmpfile1 = Path(self.tempdir / "out1.mp4")
        self.tmpfile2 = Path(self.tempdir / "out2.mp4")
        video_data = VideoData(video_path=self.tmpfile1, data=self.data)
        self.cv = CVProcessor(
            video_data=video_data,
            path_output=self.tmpfile2,
            progress_signal=self.progress,
            parent=self,
            plot_enabled=plot_enabled,
        )

    def do_work(self):
        progress = FFmpeg().convert_video(
            path_input=self.video_file_path_input,
            path_output=self.tmpfile1,
            signal=self.progress,
            current_progress=1,
        )
        self.cv.prepare()
        progress = self.cv.run(
            current_progress=progress, start_timestamp=self.start_timestamp
        )
        FFmpeg().convert_video(
            path_input=self.tmpfile2,
            path_output=self.video_file_path_output,
            signal=self.progress,
            current_progress=progress,
        )

    def run(self):
        try:
            self.do_work()
            self.signal_finished.emit(ProcessResult(is_success=True))
        except Exception as e:
            self.signal_finished.emit(ProcessResult(is_success=False, exception=e))
        finally:
            clean(tempdir=self.tempdir)
