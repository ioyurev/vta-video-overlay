
import numpy as np

from vta_video_overlay.config import config, get_graph_size
from vta_video_overlay.data_file import Data
from vta_video_overlay.graph_overlay import GraphOverlay
from vta_video_overlay.aligned_data import AlignedData
from vta_video_overlay.video_context import VideoContext
from vta_video_overlay.opencv_frame import CVFrame
from vta_video_overlay.make_frame import make_frame


class FrameRenderer:
    """Единый рендерер кадров для Preview и Export."""
    
    def __init__(
        self,
        video_ctx: VideoContext,
        data: Data,
        timestamps: np.ndarray | None = None,  # None = linspace для preview
        crop_rect=None,
        graph_enabled: bool = True,
    ):
        self.video_ctx = video_ctx
        self.data = data
        self.crop_rect = crop_rect
        
        # Временная сетка
        if timestamps is None:
            duration = video_ctx.total_frames / video_ctx.fps
            timestamps = np.linspace(0, duration, video_ctx.total_frames)
        
        # Выровненные данные
        self.aligned = AlignedData.from_data(timestamps, data)
        
        # График
        self.graph_renderer = None
        if graph_enabled and self.aligned.speed is not None:
            frame_w = crop_rect.w if crop_rect else video_ctx.width
            frame_h = crop_rect.h if crop_rect else video_ctx.height
            g_w, g_h = get_graph_size(frame_w, frame_h)
            
            self.graph_renderer = GraphOverlay(
                data=self.aligned.speed,
                fps=video_ctx.fps,
                width=g_w,
                height=g_h,
                time_window_sec=config.graph.time_window,
            )
    
    def render_frame(self, frame_index: int) -> CVFrame | None:
        """Рендерит один кадр."""
        img = self.video_ctx.read_frame(frame_index)
        if img is None:
            return None
        
        emf, temp, speed = self.aligned.at_index(frame_index)
        
        graph_img = None
        if self.graph_renderer and config.graph.enabled:
            graph_img = self.graph_renderer.get_frame_overlay(frame_index)
        
        return make_frame(
            img=img,
            crop_rect=self.crop_rect,
            time=float(self.aligned.timestamps[frame_index]),
            emf=emf,
            temp=temp,
            temp_speed=speed,
            graph_img=graph_img,
            operator_name=f"Operator: {self.data.operator}",
            sample_name=f"Sample: {self.data.sample}",
            add_text=config.additional_text if config.additional_text_enabled else None,
        )
