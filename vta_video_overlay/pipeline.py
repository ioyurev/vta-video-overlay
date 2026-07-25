import traceback
from pathlib import Path

from loguru import logger as log
from PySide6 import QtCore

from vta_video_overlay.crop_selection_widgets import RectangleGeometry
from vta_video_overlay.data_collections import ProcessProgress, ProcessResult
from vta_video_overlay.data_file import Data
from vta_video_overlay.opencv_processor import CVProcessor
from vta_video_overlay.video_data import VideoData


class Pipeline(QtCore.QThread):
    stage_progress = QtCore.Signal(ProcessProgress)
    stage_finished = QtCore.Signal(tuple)
    work_finished = QtCore.Signal(ProcessResult)
    fps_updated = QtCore.Signal(float)
    data: Data
    video_path_input: Path
    video_path_output: Path
    crop_rect: RectangleGeometry | None = None
    graph_enabled: bool = True

    cv_agent: CVProcessor | None = None

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
        # 1. Загружаем видеоданные и привязываем временные метки
        video_data = VideoData(video_path=self.video_path_input, data=self.data)
        self.stage_finished.emit((len(video_data.timestamps) - 1, "1/1", "frame"))

        # 2. Прямой 1-стадийный рендеринг OpenCV -> FFmpeg (0 временных файлов)
        self.cv_agent = CVProcessor(
            video_data=video_data,
            path_output=self.video_path_output,
            crop_rect=self.crop_rect,
            graph_enabled=self.graph_enabled,
        )
        self.cv_agent.progress_signal.connect(self.stage_progress.emit)
        self.cv_agent.fps_signal.connect(self.fps_updated.emit)
        self.cv_agent.run()
        self.stage_finished.emit((100.0, "1/1", "%"))
