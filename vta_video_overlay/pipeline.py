import traceback
from pathlib import Path

from loguru import logger as log
from PySide6 import QtCore

from vta_video_overlay.crop_selection_widgets import RectangleGeometry
from vta_video_overlay.data_collections import ProcessProgress, ProcessResult
from vta_video_overlay.data_file import Data
from vta_video_overlay.enums import OverlapStatus
from vta_video_overlay.info_models import TimelineSelection
from vta_video_overlay.opencv_processor import CVProcessor


class Pipeline(QtCore.QThread):
    stage_progress = QtCore.Signal(ProcessProgress)
    stage_finished = QtCore.Signal(tuple)
    work_finished = QtCore.Signal(ProcessResult)
    fps_updated = QtCore.Signal(float)

    def __init__(self, parent: QtCore.QObject | None = None):
        super().__init__(parent)
        self.data: Data | None = None
        self.video_path_input: Path | None = None
        self.video_path_output: Path | None = None
        self.crop_rect: RectangleGeometry | None = None
        self.cv_agent: CVProcessor | None = None
        self.timeline: TimelineSelection | None = None

    def stop(self):
        """Отмена работы потока pipeline."""
        self.requestInterruption()
        if self.cv_agent:
            self.cv_agent.stop()

    def run(self):
        try:
            self.execute()
            self.work_finished.emit(ProcessResult(is_success=True))
        except Exception as e:
            trace_str = traceback.format_exc()
            log.exception(f"Pipeline execution failed: {e}")
            self.work_finished.emit(
                ProcessResult(is_success=False, traceback_msg=trace_str)
            )

    def execute(self):
        if self.video_path_input is None or self.video_path_output is None or self.data is None:
            raise ValueError("Pipeline inputs (video_path_input, video_path_output, data) must be specified.")
        if self.timeline is None or self.timeline.status is OverlapStatus.NONE:
            raise ValueError("No temporal overlap between video and measurement data. Export impossible.")

        self.stage_finished.emit((self.timeline.kept_frames - 1, "1/1", "frame"))

        self.cv_agent = CVProcessor(
            video_path=self.video_path_input,
            data=self.data,
            path_output=self.video_path_output,
            timeline=self.timeline,
            crop_rect=self.crop_rect,
        )
        self.cv_agent.progress_signal.connect(self.stage_progress.emit)
        self.cv_agent.fps_signal.connect(self.fps_updated.emit)
        self.cv_agent.run()
        self.stage_finished.emit((100.0, "1/1", "%"))
