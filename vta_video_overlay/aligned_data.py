from dataclasses import dataclass
from typing import Tuple, TYPE_CHECKING

import numpy as np
import pandas as pd

from vta_video_overlay.config import config

if TYPE_CHECKING:
    from vta_video_overlay.data_file import Data


def calculate_speed(x: np.ndarray, y: np.ndarray | None) -> np.ndarray | None:
    """
    Универсальный расчёт скорости (производной dy/dx) со сглаживанием.
    Используется и для исходных данных (Data), и для видео-данных (AlignedData).
    """
    if y is None:
        return None
    if len(x) < 2:
        return np.zeros_like(y)
        
    # 1. Сглаживание сигнала
    smooth_y = pd.Series(y).rolling(
        window=config.graph.temp_smoothing_window, 
        center=True, 
        min_periods=1
    ).mean().to_numpy()
    
    # 2. Производная
    raw_speed = np.gradient(smooth_y, x)
    
    # 3. Сглаживание скорости
    speed = pd.Series(raw_speed).rolling(
        window=config.graph.speed_smoothing_window, 
        center=True, 
        min_periods=1
    ).mean().to_numpy()
    
    return speed


@dataclass
class AlignedData:
    """Данные, интерполированные на временную сетку видео."""
    timestamps: np.ndarray
    emf: np.ndarray
    temp: np.ndarray | None
    speed: np.ndarray | None
    
    @classmethod
    def from_data(cls, timestamps: np.ndarray, data: "Data") -> "AlignedData":
        """Создает выровненные данные из Data."""
        emf = np.interp(timestamps, data.time, data.emf)
        
        if data.temp is not None:
            temp = np.interp(timestamps, data.time, data.temp)
            speed = calculate_speed(timestamps, temp)
        else:
            temp = None
            speed = None
        
        return cls(timestamps=timestamps, emf=emf, temp=temp, speed=speed)
    
    def at_index(self, idx: int) -> Tuple[float, float | None, float | None]:
        """Возвращает (emf, temp, speed) для кадра по индексу."""
        temp = self.temp[idx] if self.temp is not None else None
        speed = self.speed[idx] if self.speed is not None else None
        return float(self.emf[idx]), temp, speed
    
    def get_frame_context(self, idx: int, operator: str, sample: str) -> dict:
        """Возвращает kwargs для make_frame."""
        emf, temp, speed = self.at_index(idx)
        return {
            "time": float(self.timestamps[idx]),
            "emf": emf,
            "temp": temp,
            "temp_speed": speed,
            "operator_name": f"Operator: {operator}",
            "sample_name": f"Sample: {sample}",
            "add_text": config.additional_text if config.additional_text_enabled else None,
        }
