import unittest
import numpy as np
from pathlib import Path

from vta_video_overlay.data_file import Data
from vta_video_overlay.enums import OverlapStatus
from vta_video_overlay.info_builders import build_timeline_selection
from vta_video_overlay.info_models import VideoInfo


def make_data(t_start, t_end, n=1000):
    data = Data()
    data.time = np.linspace(t_start, t_end, n)
    data.emf = np.linspace(0, 10, n)
    data.temp = np.linspace(20, 1000, n)
    data.operator = "Test"
    data.sample = "VFR_Sample"
    return data


def make_vfr_video_info(timestamps: np.ndarray) -> VideoInfo:
    duration = float(timestamps[-1] - timestamps[0]) if len(timestamps) > 1 else 0.0
    avg_fps = (len(timestamps) - 1) / duration if duration > 0 else 15.0
    return VideoInfo(
        path=Path("vfr.mp4"),
        input_width=1920,
        input_height=1080,
        fps_nominal=avg_fps,
        total_frames=len(timestamps),
        duration_sec=duration,
        timestamps_source="synthetic VFR",
        timestamps_available=True,
        first_timestamp_sec=float(timestamps[0]),
        last_timestamp_sec=float(timestamps[-1]),
        timestamps_sec=timestamps,
    )


class TestVFRNativeAlignment(unittest.TestCase):
    """Нативное 1:1 сопоставление: каждый физический кадр привязывается к своему timestamp."""

    def setUp(self):
        # VFR: 5 FPS первые 50 сек, 25 FPS следующие 50 сек
        part1 = np.arange(0, 50, 0.2)        # 250 кадров
        part2 = np.arange(50, 100.04, 0.04)  # ~1251 кадр
        self.vfr_ts = np.concatenate([part1, part2])
        self.data = make_data(0, 100, 1001)

    def test_zero_frame_matching_error(self):
        """Погрешность привязки кадра к timestamp == 0."""
        video = make_vfr_video_info(self.vfr_ts)
        tl = build_timeline_selection(self.data, video)

        mapped_ts = self.vfr_ts[tl.source_frame_indices]
        error = np.abs(mapped_ts - tl.kept_timestamps_sec).max()
        self.assertEqual(error, 0.0)

    def test_all_frames_kept_on_full_overlap(self):
        """При полном пересечении все кадры сохраняются."""
        video = make_vfr_video_info(self.vfr_ts)
        tl = build_timeline_selection(self.data, video)

        self.assertIs(tl.status, OverlapStatus.FULL)
        self.assertEqual(tl.kept_frames, len(self.vfr_ts))

    def test_partial_overlap_preserves_vfr_structure(self):
        """При частичном пересечении VFR-структура сохраняется."""
        data = make_data(30, 70)
        video = make_vfr_video_info(self.vfr_ts)
        tl = build_timeline_selection(data, video)

        # Все kept_timestamps должны быть подмножеством исходных
        for ts in tl.kept_timestamps_sec:
            self.assertIn(ts, self.vfr_ts)

        # Временные промежутки kept_timestamps неравномерные (VFR)
        diffs = np.diff(tl.kept_timestamps_sec)
        self.assertFalse(np.allclose(diffs, diffs[0]),
                         "VFR timestamps should have varying intervals")


class TestVFRExtremeRateChanges(unittest.TestCase):
    """Экстремальные перепады FPS."""

    def test_1fps_to_120fps(self):
        """Резкий скачок с 1 FPS на 120 FPS."""
        part1 = np.arange(0, 10, 1.0)        # 10 кадров, 1 FPS
        part2 = np.arange(10, 11, 1/120)      # 120 кадров, 120 FPS
        ts = np.concatenate([part1, part2])
        data = make_data(0, 11)
        video = make_vfr_video_info(ts)
        tl = build_timeline_selection(data, video)

        self.assertIs(tl.status, OverlapStatus.FULL)
        self.assertEqual(tl.kept_frames, len(ts))

    def test_single_burst(self):
        """Один длинный кадр, потом пачка коротких."""
        ts = np.array([0.0, 5.0, 5.1, 5.2, 5.3, 5.4, 5.5])
        data = make_data(0, 6)
        video = make_vfr_video_info(ts)
        tl = build_timeline_selection(data, video)

        self.assertEqual(tl.kept_frames, 7)


class TestVFRDuplicateTimestamps(unittest.TestCase):
    """Видео с дублирующимися timestamps (bitmapped/broken muxer)."""

    def test_duplicate_timestamps_handled(self):
        ts = np.array([0.0, 1.0, 1.0, 2.0, 3.0, 3.0, 3.0, 4.0])
        data = make_data(0, 5)
        video = make_vfr_video_info(ts)
        tl = build_timeline_selection(data, video)

        self.assertGreater(tl.kept_frames, 0)
        # Индексы должны быть валидными
        self.assertTrue(np.all(tl.source_frame_indices < len(ts)))


class TestVFRNonZeroStart(unittest.TestCase):
    """Видео, начинающееся не с 0 секунд."""

    def test_video_starts_at_offset(self):
        """Видео начинается с 1000 секунд (характерно для записей с DVR)."""
        ts = np.linspace(1000, 1100, 500)
        data = make_data(1000, 1100)
        video = make_vfr_video_info(ts)
        tl = build_timeline_selection(data, video)

        self.assertIs(tl.status, OverlapStatus.FULL)
        self.assertEqual(tl.kept_frames, 500)

    def test_video_starts_at_offset_partial(self):
        """Видео [1000, 1100], данные [1050, 1150]."""
        ts = np.linspace(1000, 1100, 500)
        data = make_data(1050, 1150)
        video = make_vfr_video_info(ts)
        tl = build_timeline_selection(data, video)

        self.assertIs(tl.status, OverlapStatus.PARTIAL)
        self.assertAlmostEqual(tl.overlap_start_sec, 1050, places=0)
        self.assertAlmostEqual(tl.overlap_end_sec, 1100, places=0)


class TestVFRSetptsGeneration(unittest.TestCase):
    """Тестирование генерации фильтра setpts для FFmpeg."""

    def test_build_vfr_setpts_script_content(self):
        from vta_video_overlay.video_timing import build_vfr_setpts_script_content

        ts = np.array([0.0, 0.5, 1.0, 2.5, 4.0])
        script = build_vfr_setpts_script_content(ts)

        self.assertTrue(script.startswith("setpts=("))
        self.assertTrue(script.endswith(")/TB"))
        self.assertIn("gte(N\\,0)", script)
        self.assertIn("4.0000", script)

    def test_build_vfr_setpts_single_frame(self):
        from vta_video_overlay.video_timing import build_vfr_setpts_script_content

        ts = np.array([10.0])
        script = build_vfr_setpts_script_content(ts)

        self.assertEqual(script, "setpts=N/TB")


class TestVFREncodingPTS(unittest.TestCase):
    """Интеграционный тест: проверка сохранения VFR PTS меток времени при кодировании оверлея в MP4."""

    def test_vfr_export_preserves_exact_timestamps(self):
        import cv2
        from dataclasses import replace
        from vta_video_overlay.ffmpeg_utils import FFmpeg
        from vta_video_overlay.opencv_processor import CVProcessor
        from vta_video_overlay.temp_dir_manager import TempDirManager

        tmp_dir = TempDirManager.get_temp_dir()
        input_video = tmp_dir / "synthetic_vfr_in.mp4"
        output_video = tmp_dir / "synthetic_vfr_out.mp4"

        if input_video.exists():
            input_video.unlink()
        if output_video.exists():
            output_video.unlink()

        # VFR timestamps: 25 кадров @ 5 FPS (0..5s), 50 кадров @ 25 FPS (5..7s)
        part1 = np.arange(0, 5.0, 0.2)
        part2 = np.arange(5.0, 7.04, 0.04)
        timestamps = np.concatenate([part1, part2])

        w, h = 320, 240
        writer = cv2.VideoWriter(
            str(input_video), cv2.VideoWriter_fourcc(*"mp4v"), 25.0, (w, h)  # type: ignore[attr-defined]
        )
        for i in range(len(timestamps)):
            img = np.zeros((h, w, 3), dtype=np.uint8)
            cv2.putText(
                img,
                f"F{i}",
                (20, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (255, 255, 255),
                2,
            )
            writer.write(img)
        writer.release()

        from vta_video_overlay.info_builders import build_video_info
        data = make_data(0, 10.0, 1000)
        v_info = build_video_info(input_video)
        v_info = replace(
            v_info,
            timestamps_sec=timestamps,
            duration_sec=float(timestamps[-1] - timestamps[0]),
        )

        tl = build_timeline_selection(data, v_info)

        processor = CVProcessor(
            video_path=input_video,
            data=data,
            path_output=output_video,
            timeline=tl,
        )
        processor.run()

        extracted_ms = FFmpeg().get_timestamps(output_video)
        extracted_sec = np.array(extracted_ms, dtype=float) / 1000.0

        self.assertEqual(len(extracted_sec), len(timestamps))
        max_diff = float(np.abs(extracted_sec - timestamps).max())
        self.assertLess(max_diff, 0.05, f"VFR PTS difference too high: {max_diff:.4f}s")


if __name__ == "__main__":
    unittest.main()


