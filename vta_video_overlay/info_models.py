from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from vta_video_overlay.crop_selection_widgets import RectangleGeometry
from vta_video_overlay.data_file import Data
from vta_video_overlay.enums import OverlapStatus


@dataclass(slots=True)
class MeasurementInfo:
    source_format: str
    version: str
    path: Path
    sample: str
    operator: str
    points: int
    t_min_sec: float
    t_max_sec: float
    duration_sec: float
    emf_min: float | None
    emf_max: float | None
    temp_available: bool
    temp_min: float | None
    temp_max: float | None
    calibration_available: bool
    calibration_type: str | None = None
    calibration_semantics: str | None = None
    calibration_coeffs_text: str | None = None
    thermocouple_coeffs_text: str | None = None
    cjc_text: str | None = None


@dataclass(slots=True)
class VideoInfo:
    # --- Input ---
    path: Path
    input_width: int
    input_height: int
    fps_nominal: float
    real_fps: float | None = None
    total_frames: int = 0
    duration_sec: float = 0.0
    timestamps_source: str = ""
    timestamps_available: bool = False
    first_timestamp_sec: float | None = None
    last_timestamp_sec: float | None = None
    crop_rect: RectangleGeometry | None = None
    codec_name: str | None = None
    pix_fmt: str | None = None
    timestamps_sec: np.ndarray = field(
        repr=False, default_factory=lambda: np.array([], dtype=float)
    )

    # --- Used (after overlap) ---
    used_start_sec: float | None = None
    used_end_sec: float | None = None
    kept_frames: int | None = None
    kept_duration_sec: float | None = None
    trimmed_start_frames: int = 0
    trimmed_end_frames: int = 0

    @property
    def output_width(self) -> int:
        return self.crop_rect.w if self.crop_rect else self.input_width

    @property
    def output_height(self) -> int:
        return self.crop_rect.h if self.crop_rect else self.input_height


@dataclass(slots=True)
class TimelineSelection:
    """Описание пересечения временных интервалов видео и данных."""

    status: OverlapStatus
    overlap_start_sec: float
    overlap_end_sec: float
    overlap_duration_sec: float
    source_frame_indices: np.ndarray  # индексы кадров исходного видео
    kept_timestamps_sec: np.ndarray  # timestamps сохранённых кадров
    kept_frames: int
    trimmed_start_frames: int
    trimmed_end_frames: int
    data_discarded_before_sec: float  # сколько секунд данных до overlap
    data_discarded_after_sec: float  # сколько секунд данных после overlap
    video_trimmed_at_start: bool
    video_trimmed_at_end: bool
    error_message: str | None = None


@dataclass(slots=True)
class AlignedInfo:
    points: int
    t_min_sec: float
    t_max_sec: float
    duration_sec: float
    interpolation: str
    normalized_timestamps: bool
    temp_available: bool
    speed_available: bool
    real_fps: float | None
    temp_smoothing_window: int
    speed_smoothing_window: int
    overlap_status: OverlapStatus
    trimmed_start_frames: int
    trimmed_end_frames: int
    data_discarded_before_sec: float
    data_discarded_after_sec: float
    video_trimmed_at_start: bool
    video_trimmed_at_end: bool
    error_message: str | None = None


@dataclass(slots=True)
class LoadedMeasurement:
    data: Data
    info: MeasurementInfo


@dataclass(slots=True)
class SessionState:
    """Полное состояние текущей сессии."""

    measurement: LoadedMeasurement | None = None
    video_info: VideoInfo | None = None
    timeline: TimelineSelection | None = None
    aligned_info: AlignedInfo | None = None

