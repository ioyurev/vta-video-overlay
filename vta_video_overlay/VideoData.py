from .TdaFile import Data
from .FFmpeg import FFmpeg
from PySide6 import QtCore
from pathlib import Path
import numpy as np
from loguru import logger as log


class VideoData(QtCore.QObject):
    def __init__(self, video_path: Path, data: Data):
        super().__init__()
        self.data = data
        self.operator = data.operator
        self.sample = data.sample
        self.path = video_path
        self.temp_enabled = data.temp_enabled

    def prepare(self):
        self.timestamps = np.array(FFmpeg().get_timestamps(self.path)) / 1000
        log.info(
            self.tr("Number of video frames: {len}").format(len=len(self.timestamps))
        )
        self.emf_aligned = np.interp(
            self.timestamps, self.data.data_time, self.data.data_emf
        )
        self.temp_aligned = np.interp(
            self.timestamps, self.data.data_time, self.data.data_temp
        )
        self.dE_per_dt = np.gradient(self.emf_aligned, self.timestamps)
