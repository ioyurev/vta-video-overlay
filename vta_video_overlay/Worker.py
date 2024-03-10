from vta_video_overlay.TdaFile import Data
from vta_video_overlay.OpenCV import CVProcessor
from vta_video_overlay.FFmpeg import convert_video
from vta_video_overlay.VideoData import VideoData
from pathlib import Path
from PySide6 import QtCore
import tempfile
import shutil
import os


def clean(tempdir: str):
    if os.path.exists(tempdir):
        shutil.rmtree(tempdir)


class Worker(QtCore.QThread):
    progress = QtCore.Signal(int)
    step_done = QtCore.Signal(int)

    def __init__(
        self,
        parent,
        video_file_path_input: Path,
        video_file_path_output: Path,
        data: Data,
    ):
        super().__init__(parent=parent)
        self.video_file_path_input = video_file_path_input
        self.video_file_path_output = video_file_path_output
        self.data = data

    def do_work(self, tmpfile1: Path, tmpfile2: Path):
        progress = convert_video(
            path_input=self.video_file_path_input,
            path_output=tmpfile1,
            signal=self.progress,
            current_progress=1,
        )
        self.step_done.emit(progress)
        video_data = VideoData(video_path=tmpfile1, data=self.data)
        cv = CVProcessor(
            video_data=video_data, path_output=tmpfile2, progress_signal=self.progress
        )
        progress = cv.run(current_progress=progress)
        self.step_done.emit(progress)
        convert_video(
            path_input=tmpfile2,
            path_output=self.video_file_path_output,
            signal=self.progress,
            current_progress=progress,
        )

    def run(self):
        with tempfile.TemporaryDirectory() as tempdir:
            tmpfile1 = Path(tempdir + "/out1.mp4")
            tmpfile2 = Path(tempdir + "/out2.mp4")
            self.do_work(tmpfile1=tmpfile1, tmpfile2=tmpfile2)
            clean(tempdir=tempdir)
