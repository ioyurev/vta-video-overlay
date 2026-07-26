from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from loguru import logger as log

from vta_video_overlay.aligned_data import calculate_speed
from vta_video_overlay.excel_exporter import export_data_to_excel


@dataclass
class Data:
    operator: str = ""
    sample: str = ""
    path: Path = field(default_factory=Path)
    time: np.ndarray = field(default_factory=lambda: np.array([], dtype=float))
    emf: np.ndarray = field(default_factory=lambda: np.array([], dtype=float))
    temp: np.ndarray | None = None

    @property
    def speed(self) -> np.ndarray | None:
        """
        Ленивый расчёт скорости по исходным данным.
        Используется ТОЛЬКО для диалога предпросмотра данных.
        """
        if self.temp is None:
            return None

        speed = calculate_speed(self.time, self.temp)
        if speed is not None:
            log.info(f"Raw data speed calculated: {len(speed)} points")
        return speed

    def to_excel(self, path: Path):
        export_data_to_excel(self, path)
