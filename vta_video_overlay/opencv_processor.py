from pathlib import Path
from typing import Final
import time

import cv2
from loguru import logger as log
from PySide6 import QtCore

from vta_video_overlay.crop_selection_widgets import RectangleGeometry
from vta_video_overlay.data_collections import ProcessProgress
from vta_video_overlay.video_data import VideoData
from vta_video_overlay.video_context import VideoContext
from vta_video_overlay.frame_renderer import FrameRenderer

CODEC: Final = "mp4v"


class CVProcessor(QtCore.QObject):
    progress_signal = QtCore.Signal(ProcessProgress)
    fps_signal = QtCore.Signal(float)

    def __init__(
        self,
        video_data: VideoData,
        path_output: Path,
        crop_rect: RectangleGeometry | None = None,
        graph_enabled: bool = True,
    ):
        super().__init__()
        self.video_data = video_data
        self.path_output = path_output
        self.crop_rect = crop_rect
        self.graph_enabled = graph_enabled

    def run(self):
        # Открываем видео
        video_ctx = VideoContext.open(self.video_data.path)
        
        # Создаем рендерер
        renderer = FrameRenderer(
            video_ctx=video_ctx,
            data=self.video_data.data,
            timestamps=self.video_data.aligned.timestamps,
            crop_rect=self.crop_rect,
            graph_enabled=self.graph_enabled,
        )
        
        # Размер после кропа
        if self.crop_rect:
            size = (self.crop_rect.w, self.crop_rect.h)
        else:
            size = (video_ctx.width, video_ctx.height)
        
        # Создаем writer
        writer = cv2.VideoWriter(
            str(self.path_output),
            cv2.VideoWriter_fourcc(*CODEC),
            video_ctx.fps,
            size,
        )
        
        # --- FPS TRACKING ---
        frame_times: list[float] = []
        fps_update_interval = 10
        
        # Рендерим кадры
        for idx in range(video_ctx.total_frames):
            frame_start = time.perf_counter()
            
            frame = renderer.render_frame(idx)
            if frame:
                writer.write(frame.image)
                self.progress_signal.emit(ProcessProgress(value=idx, frame=frame))
            
            # Замер времени кадра
            frame_time = time.perf_counter() - frame_start
            frame_times.append(frame_time)
            
            # Обновляем FPS каждые N кадров
            if len(frame_times) >= fps_update_interval:
                avg_time = sum(frame_times) / len(frame_times)
                current_fps = 1.0 / avg_time if avg_time > 0 else 0.0
                self.fps_signal.emit(current_fps)
                frame_times.clear()
        
        writer.release()
        video_ctx.close()
        log.info(self.tr("OpenCV has finished"))
