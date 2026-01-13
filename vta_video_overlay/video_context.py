from pathlib import Path
from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class VideoContext:
    """Контекст видео для рендеринга."""
    cap: cv2.VideoCapture
    fps: float
    total_frames: int
    width: int
    height: int
    
    @classmethod
    def open(cls, path: str | Path) -> "VideoContext":
        """Открывает видео и создает контекст."""
        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video: {path}")
        
        return cls(
            cap=cap,
            fps=cap.get(cv2.CAP_PROP_FPS) or 30.0,
            total_frames=int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            width=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            height=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        )
    
    def read_frame(self, index: int) -> np.ndarray | None:
        """Читает кадр по индексу."""
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, index)
        ret, img = self.cap.read()
        return img if ret else None
    
    def close(self):
        """Закрывает видео."""
        if self.cap:
            self.cap.release()
