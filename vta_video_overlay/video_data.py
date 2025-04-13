"""
Video-sensor data synchronization and processing

Key Responsibilities:
- Align video frame timestamps with sensor measurements
- Manage temporal correlation between video and telemetry data
- Calculate derived metrics (e.g., dE/dt) for analysis
- Provide synchronized data access for processing pipelines

Main Components:
- VideoData: Core data container implementing:
  - Frame timestamp synchronization via FFmpeg
  - Sensor data interpolation for video alignment
  - Gradient calculations for EMF changes
  - Temperature data validation/processing

Dependencies:
- .ffmpeg_utils: Video timestamp extraction
- .tda_file: Sensor data source (Data class)
- numpy: Array operations and interpolation
- PySide6.QtCore: QObject integration

Data Flow:
1. Extract video frame timestamps using FFprobe
2. Interpolate sensor data to match video temporal resolution
3. Calculate first derivative of EMF measurements (dE/dt)
4. Validate temperature calibration status
5. Provide aligned datasets for overlay rendering
"""

from pathlib import Path

import numpy as np
from loguru import logger as log
from PySide6 import QtCore

from vta_video_overlay.ffmpeg_utils import FFmpeg
from vta_video_overlay.tda_file import Data


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
