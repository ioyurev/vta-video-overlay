from dataclasses import replace
from pathlib import Path

import cv2
import numpy as np

from vta_video_overlay.aligned_data import AlignedData
from vta_video_overlay.config import config
from vta_video_overlay.crop_selection_widgets import RectangleGeometry
from vta_video_overlay.data_file import Data
from vta_video_overlay.enums import OverlapStatus
from vta_video_overlay.ffmpeg_utils import FFmpeg
from vta_video_overlay.info_models import AlignedInfo, TimelineSelection, VideoInfo
from vta_video_overlay.video_timing import compute_real_fps


def build_video_info(
    video_path: Path,
    crop_rect: RectangleGeometry | None = None,
) -> VideoInfo:
    ff = FFmpeg()
    timestamps = np.array(ff.get_timestamps(video_path), dtype=float) / 1000.0

    cap = cv2.VideoCapture(str(video_path))
    fps_nominal = cap.get(cv2.CAP_PROP_FPS) or 30.0
    opencv_total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    video_stream = ff.get_video_stream_info(video_path)

    width = int(video_stream["width"])
    height = int(video_stream["height"])

    first_ts = float(timestamps[0]) if len(timestamps) else None
    last_ts = float(timestamps[-1]) if len(timestamps) else None

    if len(timestamps) > 0:
        total_frames = len(timestamps)
        duration_sec = (
            (last_ts - first_ts)
            if first_ts is not None and last_ts is not None and len(timestamps) > 1
            else 0.0
        )
        real_fps = compute_real_fps(timestamps)
    else:
        total_frames = max(0, opencv_total_frames)
        duration_sec = total_frames / fps_nominal if fps_nominal > 0 else 0.0
        real_fps = None

    return VideoInfo(
        path=video_path,
        input_width=width,
        input_height=height,
        fps_nominal=float(fps_nominal),
        real_fps=real_fps,
        total_frames=total_frames,
        duration_sec=float(duration_sec),
        timestamps_source="ffprobe packet timestamps",
        timestamps_available=len(timestamps) > 0,
        first_timestamp_sec=first_ts,
        last_timestamp_sec=last_ts,
        crop_rect=crop_rect,
        codec_name=video_stream.get("codec_name"),
        pix_fmt=video_stream.get("pix_fmt"),
        timestamps_sec=timestamps,
    )


def update_video_info_with_timeline(
    video_info: VideoInfo,
    timeline: TimelineSelection,
) -> VideoInfo:
    """Обновляет VideoInfo сведениями об используемом интервале."""
    return replace(
        video_info,
        used_start_sec=timeline.overlap_start_sec if timeline.status is not OverlapStatus.NONE else None,
        used_end_sec=timeline.overlap_end_sec if timeline.status is not OverlapStatus.NONE else None,
        kept_frames=timeline.kept_frames,
        kept_duration_sec=timeline.overlap_duration_sec if timeline.status is not OverlapStatus.NONE else None,
        trimmed_start_frames=timeline.trimmed_start_frames,
        trimmed_end_frames=timeline.trimmed_end_frames,
    )


def build_timeline_selection(
    data: Data,
    video_info: VideoInfo,
) -> TimelineSelection:
    """Вычисляет пересечение временных интервалов видео и данных (нативное VFR 1:1 сопоставление)."""
    video_ts = video_info.timestamps_sec
    data_time = data.time

    if len(video_ts) == 0 or len(data_time) == 0:
        return TimelineSelection(
            status=OverlapStatus.NONE,
            overlap_start_sec=0.0,
            overlap_end_sec=0.0,
            overlap_duration_sec=0.0,
            source_frame_indices=np.array([], dtype=int),
            kept_timestamps_sec=np.array([], dtype=float),
            kept_frames=0,
            trimmed_start_frames=0,
            trimmed_end_frames=0,
            data_discarded_before_sec=0.0,
            data_discarded_after_sec=0.0,
            video_trimmed_at_start=False,
            video_trimmed_at_end=False,
            error_message="No video timestamps or measurement data available.",
        )

    video_start = float(video_ts[0])
    video_end = float(video_ts[-1])
    data_start = float(data_time[0])
    data_end = float(data_time[-1])

    overlap_start = max(video_start, data_start)
    overlap_end = min(video_end, data_end)

    if overlap_start >= overlap_end:
        return TimelineSelection(
            status=OverlapStatus.NONE,
            overlap_start_sec=overlap_start,
            overlap_end_sec=overlap_end,
            overlap_duration_sec=0.0,
            source_frame_indices=np.array([], dtype=int),
            kept_timestamps_sec=np.array([], dtype=float),
            kept_frames=0,
            trimmed_start_frames=int(np.sum(video_ts < overlap_start)),
            trimmed_end_frames=int(np.sum(video_ts > overlap_end)),
            data_discarded_before_sec=max(0.0, video_start - data_start),
            data_discarded_after_sec=max(0.0, data_end - video_end),
            video_trimmed_at_start=data_start > video_start,
            video_trimmed_at_end=data_end < video_end,
            error_message="No temporal overlap between video and measurement data.",
        )

    overlap_duration = overlap_end - overlap_start

    # Нативное 1:1 VFR сопоставление физических кадров исходной видеозаписи
    mask = (video_ts >= overlap_start) & (video_ts <= overlap_end)
    kept_indices = np.where(mask)[0]
    kept_ts = video_ts[mask]

    trimmed_start = int(np.sum(video_ts < overlap_start - 1e-5))
    trimmed_end = int(np.sum(video_ts > overlap_end + 1e-5))

    video_trimmed_at_start = data_start > video_start
    video_trimmed_at_end = data_end < video_end

    data_discarded_before = max(0.0, video_start - data_start) if data_start < video_start - 1e-5 else 0.0
    data_discarded_after = max(0.0, data_end - video_end) if data_end > video_end + 1e-5 else 0.0

    is_full = (trimmed_start == 0 and trimmed_end == 0
               and data_discarded_before == 0.0 and data_discarded_after == 0.0)

    return TimelineSelection(
        status=OverlapStatus.FULL if is_full else OverlapStatus.PARTIAL,
        overlap_start_sec=float(overlap_start),
        overlap_end_sec=float(overlap_end),
        overlap_duration_sec=float(overlap_duration),
        source_frame_indices=kept_indices,
        kept_timestamps_sec=kept_ts,
        kept_frames=len(kept_indices),
        trimmed_start_frames=trimmed_start,
        trimmed_end_frames=trimmed_end,
        data_discarded_before_sec=data_discarded_before,
        data_discarded_after_sec=data_discarded_after,
        video_trimmed_at_start=video_trimmed_at_start,
        video_trimmed_at_end=video_trimmed_at_end,
    )


def build_aligned_info(
    data: Data,
    video_info: VideoInfo,
    timeline: TimelineSelection,
) -> AlignedInfo:
    """Строит AlignedInfo на основе уже вычисленного TimelineSelection."""
    if timeline.status is OverlapStatus.NONE:
        return AlignedInfo(
            points=0,
            t_min_sec=0.0,
            t_max_sec=0.0,
            duration_sec=0.0,
            interpolation="np.interp",
            normalized_timestamps=True,
            temp_available=False,
            speed_available=False,
            real_fps=None,
            temp_smoothing_window=config.graph.temp_smoothing_window,
            speed_smoothing_window=config.graph.speed_smoothing_window,
            overlap_status=OverlapStatus.NONE,
            trimmed_start_frames=timeline.trimmed_start_frames,
            trimmed_end_frames=timeline.trimmed_end_frames,
            data_discarded_before_sec=timeline.data_discarded_before_sec,
            data_discarded_after_sec=timeline.data_discarded_after_sec,
            video_trimmed_at_start=timeline.video_trimmed_at_start,
            video_trimmed_at_end=timeline.video_trimmed_at_end,
            error_message=timeline.error_message,
        )

    kept_ts = timeline.kept_timestamps_sec
    aligned = AlignedData.from_data(kept_ts, data)

    t_min = float(kept_ts[0])
    t_max = float(kept_ts[-1])
    duration = t_max - t_min

    real_fps = compute_real_fps(kept_ts)

    return AlignedInfo(
        points=len(kept_ts),
        t_min_sec=t_min,
        t_max_sec=t_max,
        duration_sec=duration,
        interpolation="np.interp",
        normalized_timestamps=True,
        temp_available=aligned.temp is not None,
        speed_available=aligned.speed is not None,
        real_fps=real_fps,
        temp_smoothing_window=config.graph.temp_smoothing_window,
        speed_smoothing_window=config.graph.speed_smoothing_window,
        overlap_status=timeline.status,
        trimmed_start_frames=timeline.trimmed_start_frames,
        trimmed_end_frames=timeline.trimmed_end_frames,
        data_discarded_before_sec=timeline.data_discarded_before_sec,
        data_discarded_after_sec=timeline.data_discarded_after_sec,
        video_trimmed_at_start=timeline.video_trimmed_at_start,
        video_trimmed_at_end=timeline.video_trimmed_at_end,
    )

