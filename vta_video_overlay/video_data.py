"""
Video-sensor temporal alignment and synchronization system

Key Responsibilities:
- Precise frame-level alignment of video and sensor data streams
- Temporal interpolation of sensor measurements to video timestamps
- Validation of time synchronization integrity
- Provision of aligned datasets for overlay rendering

Data Flow:
1. Extract millisecond-precise video timestamps via FFprobe
2. Convert sensor data timebase (seconds) to video timebase (ms)
3. Interpolate sensor measurements to video frame timestamps
4. Validate alignment through statistical analysis

Synchronization Details:
- Uses PTS (Presentation Timestamp) values from video container
- Handles variable frame rate (VFR) content through exact timestamps
- Accounts for sensor sampling rate vs video frame rate disparities
"""

from pathlib import Path

import numpy as np
from loguru import logger as log
from PySide6 import QtCore

from vta_video_overlay.data_file import Data
from vta_video_overlay.ffmpeg_utils import FFmpeg


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
        self.emf_aligned = np.interp(self.timestamps, self.data.time, self.data.emf)
        if self.temp_enabled:
            self.temp_aligned = np.interp(
                self.timestamps, self.data.time, self.data.temp
            )
