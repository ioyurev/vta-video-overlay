from pathlib import Path
from typing import TypedDict

import numpy as np

from vta_video_overlay.data_file import Data


class MeasurementRanges(TypedDict):
    t_min: float
    t_max: float
    emf_min: float | None
    emf_max: float | None
    temp_min: float | None
    temp_max: float | None


def build_data(
    *,
    path: Path,
    operator: str,
    sample: str,
    time: np.ndarray,
    emf: np.ndarray,
    temp: np.ndarray | None,
) -> Data:
    data = Data()
    data.path = path
    data.operator = operator
    data.sample = sample
    data.time = time
    data.emf = emf
    data.temp = temp
    return data


def compute_ranges(
    time: np.ndarray,
    emf: np.ndarray,
    temp: np.ndarray | None,
) -> MeasurementRanges:
    t_min = float(time[0]) if len(time) else 0.0
    t_max = float(time[-1]) if len(time) else 0.0
    return MeasurementRanges(
        t_min=t_min,
        t_max=t_max,
        emf_min=float(emf.min()) if len(emf) else None,
        emf_max=float(emf.max()) if len(emf) else None,
        temp_min=float(temp.min()) if temp is not None and len(temp) else None,
        temp_max=float(temp.max()) if temp is not None and len(temp) else None,
    )
