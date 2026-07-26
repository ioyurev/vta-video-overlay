import unittest
import numpy as np
from pathlib import Path

from vta_video_overlay.aligned_data import AlignedData
from vta_video_overlay.data_file import Data
from vta_video_overlay.info_builders import build_timeline_selection
from vta_video_overlay.info_models import VideoInfo


class TestDoubleIndexing(unittest.TestCase):
    """
    Имитирует полный путь:
      слайдер (kept_index) → source_frame_indices[kept_index] → VideoContext.read_frame(source_idx)
      + AlignedData.at_index(kept_index) → emf, temp, speed для этого кадра
    """

    def setUp(self):
        # Видео: [10, 90], данные: [20, 80]
        self.video_ts = np.linspace(10, 90, 801)  # 0.1s шаг, 801 кадр
        self.data = Data()
        self.data.time = np.linspace(20, 80, 601)
        self.data.emf = self.data.time * 0.5      # emf = time * 0.5
        self.data.temp = self.data.time * 10       # temp = time * 10

        self.video_info = VideoInfo(
            path=Path("test.mp4"),
            input_width=640,
            input_height=480,
            fps_nominal=10.0,
            total_frames=len(self.video_ts),
            duration_sec=80.0,
            timestamps_source="synthetic",
            timestamps_available=True,
            first_timestamp_sec=10.0,
            last_timestamp_sec=90.0,
            timestamps_sec=self.video_ts,
        )

    def test_kept_index_maps_to_correct_source_frame(self):
        tl = build_timeline_selection(self.data, self.video_info)

        # kept_index=0 → первый кадр в overlap → video_ts[source_frame_indices[0]] ≈ 20.0
        first_source = tl.source_frame_indices[0]
        self.assertAlmostEqual(self.video_ts[first_source], tl.overlap_start_sec, places=1)

        last_source = tl.source_frame_indices[-1]
        self.assertAlmostEqual(self.video_ts[last_source], tl.overlap_end_sec, places=1)

    def test_aligned_data_at_kept_index_matches_expected(self):
        tl = build_timeline_selection(self.data, self.video_info)
        aligned = AlignedData.from_data(tl.kept_timestamps_sec, self.data)

        # Для kept_index=0, timestamp ≈ 20.0, emf ≈ 10.0, temp ≈ 200.0
        emf, temp, speed = aligned.at_index(0)
        self.assertAlmostEqual(emf, 10.0, places=0)
        assert temp is not None
        self.assertAlmostEqual(temp, 200.0, places=0)

    def test_every_kept_index_has_valid_data(self):
        tl = build_timeline_selection(self.data, self.video_info)
        aligned = AlignedData.from_data(tl.kept_timestamps_sec, self.data)

        for i in range(tl.kept_frames):
            emf, temp, speed = aligned.at_index(i)
            self.assertIsNotNone(emf)
            self.assertIsNotNone(temp)
            assert temp is not None
            self.assertFalse(np.isnan(emf))
            self.assertFalse(np.isnan(temp))

    def test_monotonic_time_in_kept_timestamps(self):
        tl = build_timeline_selection(self.data, self.video_info)

        diffs = np.diff(tl.kept_timestamps_sec)
        self.assertTrue(np.all(diffs >= 0),
                        "kept_timestamps_sec must be monotonically non-decreasing")


if __name__ == "__main__":
    unittest.main()
