from vta_video_overlay.TdaFile import Data
from vta_video_overlay.FFmpeg import get_timestamps
from pathlib import Path
import numpy as np


def fit_data(video_path: Path, data: Data):
    timestamps = np.array(get_timestamps(video_path)) / 1000
    print(f"* Количество кадров видео: {len(timestamps)}")
    emf_aligned = np.interp(timestamps, data.data_time, data.data_emf)
    temp_aligned = np.interp(timestamps, data.data_time, data.data_temp)
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
