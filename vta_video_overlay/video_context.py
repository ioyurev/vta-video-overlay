from pathlib import Path
from dataclasses import dataclass, field

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
    _last_index: int = field(default=-1, init=False)
    _last_img: np.ndarray | None = field(default=None, init=False)
    
    @classmethod
    def open(cls, path: str | Path) -> "VideoContext":
        """Открывает видео и создает контекст."""
        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video: {path}")
        
        fps_val = cap.get(cv2.CAP_PROP_FPS)
        total_frames_val = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width_val = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height_val = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        return cls(
            cap=cap,
            fps=fps_val if fps_val > 0 else 30.0,
            total_frames=max(0, total_frames_val),
            width=max(0, width_val),
            height=max(0, height_val),
        )
    
    def read_frame(self, index: int) -> np.ndarray | None:
        """Читает кадр по индексу с кэшированием и последовательным пропуском кадров."""
        if index == self._last_index and self._last_img is not None:
            return self._last_img.copy()

        diff = index - self._last_index
        if 0 < diff <= 60:
            img = None
            for _ in range(diff):
                ret, frame = self.cap.read()
                if not ret:
                    self._last_index = -1
                    self._last_img = None
                    return None
                img = frame
            if img is not None:
                self._last_index = index
                self._last_img = img
                return img.copy()

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, index)
        ret, img = self.cap.read()
        if ret and img is not None:
            self._last_index = index
            self._last_img = img
            return img.copy()
        return None
    
    def close(self):
        """Закрывает видео."""
        if self.cap:
            self.cap.release()
            self._last_img = None
