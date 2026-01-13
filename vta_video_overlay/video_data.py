from pathlib import Path

import numpy as np
from loguru import logger as log
from PySide6 import QtCore

from vta_video_overlay.data_file import Data
from vta_video_overlay.ffmpeg_utils import FFmpeg
from vta_video_overlay.aligned_data import AlignedData


class VideoData(QtCore.QObject):
    """Обёртка над AlignedData для обратной совместимости."""
    
    def __init__(self, video_path: Path, data: Data):
        super().__init__()
        self.data = data
        self.path = video_path
        
        # Получаем таймштампы (в секундах)
        timestamps = np.array(FFmpeg().get_timestamps(self.path)) / 1000
        
        log.info(
            self.tr("Number of video frames: {len}").format(len=len(timestamps))
        )
        
        # Создаем выровненные данные
        self.aligned = AlignedData.from_data(timestamps, data)
        
        # Прокси-свойства для обратной совместимости
        self.operator = data.operator
        self.sample = data.sample
        self.timestamps = timestamps
        self.emf_aligned = self.aligned.emf
        self.temp_aligned = self.aligned.temp
        self.temp_speed_aligned = self.aligned.speed
