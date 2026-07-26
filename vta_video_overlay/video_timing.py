import numpy as np


def compute_real_fps(timestamps_sec: np.ndarray) -> float | None:
    if len(timestamps_sec) < 2:
        return None
    duration = float(timestamps_sec[-1] - timestamps_sec[0])
    if duration <= 0:
        return None
    return (len(timestamps_sec) - 1) / duration
