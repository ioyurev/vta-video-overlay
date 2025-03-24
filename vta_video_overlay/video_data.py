from pathlib import Path

import numpy as np
from loguru import logger as log
from PySide6 import QtCore

from .ffmpeg_utils import FFmpeg
from .tda_file import Data


class VideoData(QtCore.QObject):
    def __init__(self, video_path: Path, data: Data):
        super().__init__()
        self.data = data
        self.operator = data.operator
        self.sample = data.sample
        self.path = video_path
        self.temp_enabled = data.temp_enabled
        self.timestamps = np.array(FFmpeg().get_timestamps(self.path)) / 1000
        log.info(
            self.tr("Number of video frames: {len}").format(len=len(self.timestamps))
        )
        self.emf_aligned = np.interp(
            self.timestamps, self.data.data_time, self.data.data_emf
        )
        if self.temp_enabled:
            self.temp_aligned = np.interp(
                self.timestamps, self.data.data_time, self.data.data_temp
            )
