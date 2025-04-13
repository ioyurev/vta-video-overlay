import os
import shutil
import tempfile
import traceback
from pathlib import Path

from loguru import logger as log
from PySide6 import QtCore

from vta_video_overlay.crop_selection_widgets import RectangleGeometry
from vta_video_overlay.data_collections import ProcessProgress, ProcessResult
from vta_video_overlay.ffmpeg_utils import FFmpeg
from vta_video_overlay.opencv_processor import CVProcessor
from vta_video_overlay.tda_file import Data
from vta_video_overlay.video_data import VideoData


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
    crop_rect: RectangleGeometry | None = None

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

        video_data = self._preconvert(tmpfile=tmpfile1)
        self._cv_overlay(video_data=video_data, tmpfile=tmpfile2)
        self._final_convert(tmpfile=tmpfile2)

    def _preconvert(self, tmpfile: Path):
        if FFmpeg().check_for_packets(video_path=self.video_path_input):
            file_to_overlay = self.video_path_input
            self.stage_progress.emit(ProcessProgress(value=100, frame=None))
            log.debug(self.tr("Skipped pre-conversion (timestamps exist)"))
        else:
            file_to_overlay = tmpfile
            log.warning("Input video has no timestamps. Preconverting video...")
            FFmpeg().convert_video(
                path_input=self.video_path_input,
                path_output=file_to_overlay,
                signal=self.stage_progress,
            )
        video_data = VideoData(video_path=file_to_overlay, data=self.data)
        self.stage_finished.emit((len(video_data.timestamps) - 1, "2/3", "frame"))
        return video_data

    def _cv_overlay(self, video_data: VideoData, tmpfile: Path):
        cv_agent = CVProcessor(
            video_data=video_data,
            path_output=tmpfile,
            crop_rect=self.crop_rect,
        )
        cv_agent.progress_signal.connect(self.stage_progress.emit)
        cv_agent.run()
        self.stage_finished.emit((100.0, "3/3", "%"))
        return

    def _final_convert(self, tmpfile: Path):
        FFmpeg().convert_video(
            path_input=tmpfile,
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
