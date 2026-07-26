import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from loguru import logger as log
from PySide6 import QtCore

from vta_video_overlay.config import config
from vta_video_overlay.crop_selection_widgets import RectangleGeometry, ensure_even
from vta_video_overlay.data_collections import ProcessProgress
from vta_video_overlay.data_file import Data
from vta_video_overlay.ffmpeg_utils import build_codec_args
from vta_video_overlay.frame_renderer import FrameRenderer
from vta_video_overlay.info_models import TimelineSelection
from vta_video_overlay.opencv_frame import CVFrame
from vta_video_overlay.video_context import VideoContext
from vta_video_overlay.video_timing import compute_real_fps


class CVProcessor(QtCore.QObject):
    progress_signal = QtCore.Signal(ProcessProgress)
    fps_signal = QtCore.Signal(float)

    def __init__(
        self,
        video_path: Path,
        data: Data,
        path_output: Path,
        timeline: TimelineSelection,
        crop_rect: RectangleGeometry | None = None,
    ):
        super().__init__()
        self.video_path = video_path
        self.data = data
        self.path_output = path_output
        self.timeline = timeline
        self.crop_rect = crop_rect
        self.is_interrupted = False

    def stop(self):
        """Флаг принудительной отмены обработки."""
        self.is_interrupted = True

    def run(self):
        # Открываем видео
        video_ctx = VideoContext.open(self.video_path)

        # Создаем рендерер
        renderer = FrameRenderer(
            video_ctx=video_ctx,
            data=self.data,
            timestamps=self.timeline.kept_timestamps_sec,
            crop_rect=self.crop_rect,
            graph_enabled=config.graph.enabled,
        )

        # Размер после кропа (гарантируем ЧЕТНЫЕ ширину и высоту для YUV420P / HEVC / AMF)
        if self.crop_rect:
            size = (ensure_even(self.crop_rect.w), ensure_even(self.crop_rect.h))
        else:
            size = (ensure_even(video_ctx.width), ensure_even(video_ctx.height))

        # Для VFR-видео (переменная экспозиция камеры) CAP_PROP_FPS возвращает
        # номинальный FPS, а не реальный. Вычисляем средний FPS из timestamps.
        ts = self.timeline.kept_timestamps_sec
        real_fps = compute_real_fps(ts) or video_ctx.fps

        # Подготавливаем команду FFmpeg для прямого кодирования из stdin
        cmd = [
            "ffmpeg",
            "-y",
            "-threads",
            "1",
            "-f",
            "rawvideo",
            "-vcodec",
            "rawvideo",
            "-s",
            f"{size[0]}x{size[1]}",
            "-pix_fmt",
            "bgr24",
            "-r",
            str(real_fps),
            "-i",
            "-",
            "-c:v",
            config.video_encoding.codec,
            *build_codec_args(
                config.video_encoding.codec,
                config.video_encoding.crf,
                config.video_encoding.preset,
            ),
            "-pix_fmt",
            config.video_encoding.pix_fmt,
            str(self.path_output),
        ]

        log.info(
            f"Starting direct FFmpeg pipe encoding ({config.video_encoding.codec}, CRF={config.video_encoding.crf}, threads={config.video_encoding.render_threads})..."
        )
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

        # --- STREAMING BATCH PARALLEL RENDERING ---
        num_threads = max(1, config.video_encoding.render_threads)
        batch_size = max(4, num_threads * 2)

        def _overlay_worker(args: tuple[int, np.ndarray]) -> tuple[int, CVFrame | None]:
            idx, raw_frame = args
            return idx, renderer.render_overlay(raw_frame, idx)

        source_indices = self.timeline.source_frame_indices
        max_frames = len(source_indices)

        with ThreadPoolExecutor(max_workers=num_threads) as pool:
            for batch_start in range(0, max_frames, batch_size):
                curr_thread = QtCore.QThread.currentThread()
                if self.is_interrupted or (curr_thread and curr_thread.isInterruptionRequested()):
                    log.warning("Processing interrupted by user or window close.")
                    break

                batch_end = min(batch_start + batch_size, max_frames)

                t_batch_0 = time.perf_counter()
                raw_items: list[tuple[int, np.ndarray]] = []
                for kept_i in range(batch_start, batch_end):
                    source_idx = int(source_indices[kept_i])
                    raw = video_ctx.read_frame(source_idx)
                    if raw is not None:
                        raw_items.append((kept_i, raw.copy()))

                if not raw_items:
                    continue

                results = list(pool.map(_overlay_worker, raw_items))
                results.sort(key=lambda x: x[0])

                t_batch_elapsed = time.perf_counter() - t_batch_0
                if len(results) > 0 and t_batch_elapsed > 0:
                    batch_fps = len(results) / t_batch_elapsed
                    self.fps_signal.emit(batch_fps)

                for idx, frame in results:
                    if frame and proc.stdin:
                        try:
                            proc.stdin.write(frame.image.tobytes())
                            self.progress_signal.emit(
                                ProcessProgress(value=idx, frame=frame)
                            )
                        except Exception as e:
                            log.debug(f"Error writing to FFmpeg stdin: {e}")
                            break

        if proc.stdin:
            try:
                proc.stdin.close()
            except Exception as e:
                log.debug(f"Error closing FFmpeg stdin: {e}")

        curr_thread = QtCore.QThread.currentThread()
        if self.is_interrupted or (curr_thread and curr_thread.isInterruptionRequested()):
            proc.terminate()

        proc.wait()

        video_ctx.close()
        if not (self.is_interrupted or (curr_thread and curr_thread.isInterruptionRequested())):
            log.info(self.tr("OpenCV & FFmpeg Pipe rendering finished successfully"))

