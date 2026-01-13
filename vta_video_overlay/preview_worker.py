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

    @QtCore.Slot()
    def init_video(self):
        """Открывает видео в рабочем потоке."""
        self.video_ctx = VideoContext.open(self.video_path)

    @QtCore.Slot(object, object)
    def update_data(self, data, crop_rect=None):
        """Обновляет данные и пересоздает рендерер."""
        if data is None or self.video_ctx is None:
            self.renderer = None
            return
        
        self.renderer = FrameRenderer(
            video_ctx=self.video_ctx,
            data=data,
            timestamps=None,  # linspace для preview
            crop_rect=crop_rect,
            graph_enabled=config.graph.enabled,
        )

    @QtCore.Slot(int, object, object)
    def request_frame(self, frame_index: int, data, crop_rect):
        """Генерирует кадр."""
        # Проверяем, нужно ли пересоздать рендерер
        # Это нужно, если рендерера нет, ИЛИ если изменился кроп
        needs_update = (
            self.renderer is None 
            or self.renderer.crop_rect != crop_rect
        )

        if needs_update:
            self.update_data(data, crop_rect)
        
        if self.renderer is None:
            return
        
        frame = self.renderer.render_frame(frame_index)
        if frame:
            time_sec = frame_index / self.video_ctx.fps
            self.frame_ready.emit(frame.to_pixmap(), time_sec)

    def cleanup(self):
        if self.video_ctx:
            self.video_ctx.close()
        self.finished.emit()
