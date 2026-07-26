import unittest
import numpy as np
from pathlib import Path

from vta_video_overlay.data_file import Data
from vta_video_overlay.enums import OverlapStatus
from vta_video_overlay.info_builders import build_timeline_selection
from vta_video_overlay.info_models import VideoInfo


def make_data(t_start: float, t_end: float, n_points: int = 1000) -> Data:
    """Создаёт синтетические данные измерений."""
    data = Data()
    data.time = np.linspace(t_start, t_end, n_points)
    data.emf = np.sin(data.time) * 10
    data.temp = data.time * 5 + 20
    data.operator = "Test"
    data.sample = "Sample"
    return data


def make_video_info(
    timestamps: np.ndarray,
    fps: float = 25.0,
) -> VideoInfo:
    """Создаёт синтетический VideoInfo с заданными timestamps."""
    return VideoInfo(
        path=Path("test.mp4"),
        input_width=1920,
        input_height=1080,
        fps_nominal=fps,
        total_frames=len(timestamps),
        duration_sec=float(timestamps[-1] - timestamps[0]) if len(timestamps) > 1 else 0.0,
        timestamps_source="synthetic",
        timestamps_available=True,
        first_timestamp_sec=float(timestamps[0]) if len(timestamps) else None,
        last_timestamp_sec=float(timestamps[-1]) if len(timestamps) else None,
        timestamps_sec=timestamps,
    )


class TestFullOverlap(unittest.TestCase):
    """Видео и данные полностью совпадают по времени."""

    def test_identical_ranges(self):
        data = make_data(0, 100)
        video = make_video_info(np.linspace(0, 100, 500))
        tl = build_timeline_selection(data, video)

        self.assertIs(tl.status, OverlapStatus.FULL)
        self.assertEqual(tl.kept_frames, 500)
        self.assertEqual(tl.trimmed_start_frames, 0)
        self.assertEqual(tl.trimmed_end_frames, 0)
        self.assertAlmostEqual(tl.data_discarded_before_sec, 0.0)
        self.assertAlmostEqual(tl.data_discarded_after_sec, 0.0)
        self.assertFalse(tl.video_trimmed_at_start)
        self.assertFalse(tl.video_trimmed_at_end)
        self.assertIsNone(tl.error_message)

    def test_data_wider_than_video(self):
        """Данные шире видео — всё равно full, т.к. ВСЕ кадры попадают."""
        data = make_data(-10, 110)
        video = make_video_info(np.linspace(0, 100, 500))
        tl = build_timeline_selection(data, video)

        self.assertIs(tl.status, OverlapStatus.FULL)
        self.assertEqual(tl.kept_frames, 500)


class TestPartialOverlap(unittest.TestCase):
    """Данные и видео пересекаются частично."""

    def test_video_starts_before_data(self):
        """Видео [0, 100], данные [30, 100]."""
        data = make_data(30, 100)
        video = make_video_info(np.linspace(0, 100, 1001))
        tl = build_timeline_selection(data, video)

        self.assertIs(tl.status, OverlapStatus.PARTIAL)
        self.assertTrue(tl.video_trimmed_at_start)
        self.assertFalse(tl.video_trimmed_at_end)
        self.assertGreater(tl.trimmed_start_frames, 0)
        self.assertEqual(tl.trimmed_end_frames, 0)
        self.assertAlmostEqual(tl.overlap_start_sec, 30.0, places=1)
        self.assertAlmostEqual(tl.overlap_end_sec, 100.0, places=1)

    def test_video_ends_after_data(self):
        """Видео [0, 100], данные [0, 70]."""
        data = make_data(0, 70)
        video = make_video_info(np.linspace(0, 100, 1001))
        tl = build_timeline_selection(data, video)

        self.assertIs(tl.status, OverlapStatus.PARTIAL)
        self.assertFalse(tl.video_trimmed_at_start)
        self.assertTrue(tl.video_trimmed_at_end)
        self.assertEqual(tl.trimmed_start_frames, 0)
        self.assertGreater(tl.trimmed_end_frames, 0)

    def test_data_starts_before_video(self):
        """Данные [0, 100], видео [20, 100]. Данные обрезаются в начале, но все кадры видео сохраняются."""
        data = make_data(0, 100)
        video = make_video_info(np.linspace(20, 100, 500))
        tl = build_timeline_selection(data, video)

        self.assertIs(tl.status, OverlapStatus.FULL)
        self.assertGreater(tl.data_discarded_before_sec, 0)

    def test_data_ends_after_video(self):
        """Данные [0, 120], видео [0, 80]. Все кадры видео сохраняются."""
        data = make_data(0, 120)
        video = make_video_info(np.linspace(0, 80, 500))
        tl = build_timeline_selection(data, video)

        self.assertIs(tl.status, OverlapStatus.FULL)
        self.assertGreater(tl.data_discarded_after_sec, 0)

    def test_both_sides_trimmed(self):
        """Данные [20, 80], видео [0, 100]. Видео обрезается с обеих сторон."""
        data = make_data(20, 80)
        video = make_video_info(np.linspace(0, 100, 1001))
        tl = build_timeline_selection(data, video)

        self.assertIs(tl.status, OverlapStatus.PARTIAL)
        self.assertTrue(tl.video_trimmed_at_start)
        self.assertTrue(tl.video_trimmed_at_end)
        self.assertGreater(tl.trimmed_start_frames, 0)
        self.assertGreater(tl.trimmed_end_frames, 0)
        self.assertAlmostEqual(tl.overlap_start_sec, 20.0, places=1)
        self.assertAlmostEqual(tl.overlap_end_sec, 80.0, places=1)

    def test_narrow_overlap(self):
        """Данные [0, 10], видео [9, 100]. Пересечение 1 секунда."""
        data = make_data(0, 10)
        video = make_video_info(np.linspace(9, 100, 500))
        tl = build_timeline_selection(data, video)

        self.assertIs(tl.status, OverlapStatus.PARTIAL)
        self.assertGreater(tl.kept_frames, 0)
        self.assertAlmostEqual(tl.overlap_start_sec, 9.0, places=1)
        self.assertAlmostEqual(tl.overlap_end_sec, 10.0, places=1)


class TestNoOverlap(unittest.TestCase):
    """Нет пересечения между видео и данными."""

    def test_video_after_data(self):
        data = make_data(0, 50)
        video = make_video_info(np.linspace(60, 100, 500))
        tl = build_timeline_selection(data, video)

        self.assertIs(tl.status, OverlapStatus.NONE)
        self.assertEqual(tl.kept_frames, 0)
        self.assertEqual(len(tl.source_frame_indices), 0)
        self.assertEqual(len(tl.kept_timestamps_sec), 0)

    def test_data_after_video(self):
        data = make_data(200, 300)
        video = make_video_info(np.linspace(0, 100, 500))
        tl = build_timeline_selection(data, video)

        self.assertIs(tl.status, OverlapStatus.NONE)

    def test_adjacent_but_not_overlapping(self):
        """Данные заканчиваются ровно когда начинается видео."""
        data = make_data(0, 50)
        video = make_video_info(np.linspace(50, 100, 500))
        tl = build_timeline_selection(data, video)

        # overlap_start == overlap_end == 50 → overlap_start >= overlap_end → NONE
        self.assertIs(tl.status, OverlapStatus.NONE)


class TestEdgeCases(unittest.TestCase):

    def test_empty_video_timestamps(self):
        data = make_data(0, 100)
        video = make_video_info(np.array([], dtype=float))
        tl = build_timeline_selection(data, video)

        self.assertIs(tl.status, OverlapStatus.NONE)
        self.assertIsNotNone(tl.error_message)

    def test_empty_data(self):
        data = Data()
        video = make_video_info(np.linspace(0, 100, 500))
        tl = build_timeline_selection(data, video)

        self.assertIs(tl.status, OverlapStatus.NONE)

    def test_single_frame_video(self):
        data = make_data(0, 100)
        video = make_video_info(np.array([50.0]))
        tl = build_timeline_selection(data, video)

        # Один кадр → overlap_start == overlap_end → NONE (по текущей логике)
        # или FULL если логика позволяет. Проверяем контракт:
        self.assertIn(tl.status, (OverlapStatus.NONE, OverlapStatus.FULL))

    def test_single_data_point(self):
        data = Data()
        data.time = np.array([50.0])
        data.emf = np.array([1.0])
        data.temp = np.array([100.0])
        video = make_video_info(np.linspace(0, 100, 500))
        tl = build_timeline_selection(data, video)

        self.assertIn(tl.status, (OverlapStatus.NONE, OverlapStatus.FULL))

    def test_very_large_offset(self):
        """Данные со сдвигом в миллионы секунд."""
        data = make_data(1_000_000, 1_000_100)
        video = make_video_info(np.linspace(1_000_000, 1_000_100, 500))
        tl = build_timeline_selection(data, video)

        self.assertIs(tl.status, OverlapStatus.FULL)
        self.assertEqual(tl.kept_frames, 500)


class TestFrameIndicesIntegrity(unittest.TestCase):
    """Проверяет корректность source_frame_indices."""

    def test_indices_are_valid(self):
        data = make_data(20, 80)
        ts = np.linspace(0, 100, 1001)
        video = make_video_info(ts)
        tl = build_timeline_selection(data, video)

        # Все индексы в пределах [0, len(ts))
        self.assertTrue(np.all(tl.source_frame_indices >= 0))
        self.assertTrue(np.all(tl.source_frame_indices < len(ts)))

    def test_indices_are_sorted(self):
        data = make_data(10, 90)
        video = make_video_info(np.linspace(0, 100, 500))
        tl = build_timeline_selection(data, video)

        diffs = np.diff(tl.source_frame_indices)
        self.assertTrue(np.all(diffs > 0), "source_frame_indices must be strictly sorted")

    def test_indices_map_to_correct_timestamps(self):
        """Ключевой тест: kept_timestamps_sec == video_ts[source_frame_indices]."""
        data = make_data(10, 90)
        ts = np.linspace(0, 100, 500)
        video = make_video_info(ts)
        tl = build_timeline_selection(data, video)

        expected = ts[tl.source_frame_indices]
        np.testing.assert_array_equal(tl.kept_timestamps_sec, expected)

    def test_kept_frames_equals_len_indices(self):
        data = make_data(10, 90)
        video = make_video_info(np.linspace(0, 100, 500))
        tl = build_timeline_selection(data, video)

        self.assertEqual(tl.kept_frames, len(tl.source_frame_indices))
        self.assertEqual(tl.kept_frames, len(tl.kept_timestamps_sec))

    def test_trimmed_plus_kept_equals_total(self):
        """trimmed_start + kept + trimmed_end == total_frames."""
        data = make_data(20, 80)
        ts = np.linspace(0, 100, 1001)
        video = make_video_info(ts)
        tl = build_timeline_selection(data, video)

        total_accounted = tl.trimmed_start_frames + tl.kept_frames + tl.trimmed_end_frames
        self.assertEqual(total_accounted, len(ts))


class TestSymmetry(unittest.TestCase):
    """Если поменять местами «кто шире» — результат overlap одинаков."""

    def test_overlap_symmetric(self):
        ts = np.linspace(0, 100, 500)
        data_wide = make_data(-10, 110)
        data_narrow = make_data(20, 80)

        tl_wide = build_timeline_selection(data_wide, make_video_info(ts))
        tl_narrow = build_timeline_selection(data_narrow, make_video_info(ts))

        self.assertIs(tl_wide.status, OverlapStatus.FULL)
        self.assertEqual(tl_wide.kept_frames, 500)
        self.assertAlmostEqual(tl_narrow.overlap_start_sec, 20.0, places=1)
        self.assertAlmostEqual(tl_narrow.overlap_end_sec, 80.0, places=1)


if __name__ == "__main__":
    unittest.main()
