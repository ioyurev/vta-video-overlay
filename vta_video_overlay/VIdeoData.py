from vta_video_overlay.TdaFile import Data
from vta_video_overlay.Timestamps import get_timestamps
from pathlib import Path
import numpy as np
from scipy.interpolate import interp1d


def fit_data(video_path: Path, data: Data):
    timestamps = np.array(get_timestamps(video_path)) / 1000
    print(f"* Количество кадров видео: {len(timestamps)}")
    f_emf = interp1d(
        data.data_time, data.data_emf, bounds_error=False, fill_value="extrapolate"
    )
    f_temp = interp1d(
        data.data_time, data.data_temp, bounds_error=False, fill_value="extrapolate"
    )
    emf_aligned = f_emf(timestamps)
    temp_aligned = f_temp(timestamps)
    return timestamps, emf_aligned, temp_aligned


class VideoData:
    def __init__(self, video_path: Path, data: Data):
        self.timestamps, self.emf_aligned, self.temp_aligned = fit_data(
            video_path=video_path, data=data
        )
        self.operator = data.operator
        self.sample = data.sample
        self.path = video_path
        self.temp_enabled = data.temp_enabled
