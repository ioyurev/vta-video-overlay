from PySide6 import QtCore

from vta_video_overlay.config import config
from vta_video_overlay.video_context import VideoContext
from vta_video_overlay.frame_renderer import FrameRenderer


class PreviewWorker(QtCore.QObject):
    # Сигнал: (QPixmap кадра, текущее время)
    frame_ready = QtCore.Signal(object, float)
    finished = QtCore.Signal()

    def __init__(self, video_path: str):
        super().__init__()
        self.video_path = video_path
        self.video_ctx: VideoContext | None = None
        self.renderer: FrameRenderer | None = None
        self.latest_requested_index: int = -1
        self._last_data = None
        self._last_timeline = None

    @QtCore.Slot()
    def init_video(self):
        """Открывает видео в рабочем потоке."""
        self.video_ctx = VideoContext.open(self.video_path)

    @QtCore.Slot(object, object, object)
    def update_data(self, data, crop_rect=None, timeline=None):
        """Обновляет данные и пересоздает рендерер."""
        self._last_data = data
        self._last_timeline = timeline
        if data is None or self.video_ctx is None:
            self.renderer = None
            return

        if timeline is not None and timeline.status != "none":
            timestamps = timeline.kept_timestamps_sec
        else:
            timestamps = None

        self.renderer = FrameRenderer(
            video_ctx=self.video_ctx,
            data=data,
            timestamps=timestamps,
            crop_rect=crop_rect,
            graph_enabled=config.graph.enabled,
        )

    @QtCore.Slot(int, object, object, object)
    def request_frame(self, frame_index: int, data, crop_rect, timeline):
        """Генерирует кадр.

        frame_index — индекс внутри kept subset (0..kept_frames-1).
        """
        self.latest_requested_index = frame_index

        needs_update = (
            self.renderer is None
            or self.renderer.crop_rect != crop_rect
            or self._last_data is not data
            or self._last_timeline is not timeline
        )

        if needs_update:
            self.update_data(data, crop_rect, timeline)

        if self.renderer is None:
            return

        # Перевод индекса kept -> индекс исходного видео
        if timeline is not None and timeline.status != "none":
            if frame_index >= len(timeline.source_frame_indices):
                return
            source_idx = int(timeline.source_frame_indices[frame_index])
            time_sec = float(timeline.kept_timestamps_sec[frame_index])
        else:
            source_idx = frame_index
            time_sec = frame_index / self.video_ctx.fps if self.video_ctx else 0.0

        img = self.video_ctx.read_frame(source_idx) if self.video_ctx else None
        if img is None:
            return

        frame = self.renderer.render_overlay(img, frame_index)
        if frame and frame_index == self.latest_requested_index:
            self.frame_ready.emit(frame.to_pixmap(), time_sec)

    @QtCore.Slot()
    def cleanup(self):
        if self.video_ctx:
            self.video_ctx.close()
        self.finished.emit()
