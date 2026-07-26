import unittest
from pathlib import Path
import numpy as np

from vta_video_overlay.data_file import Data
from vta_video_overlay.enums import OverlapStatus
from vta_video_overlay.info_models import VideoInfo
from vta_video_overlay.info_builders import build_timeline_selection


class TestVFRSynchronization(unittest.TestCase):
    def setUp(self):
        # Создаем VFR видеоряд длительностью 100 секунд.
        # Первые 50 секунд FPS = 5.0 (дельта 0.2с), вторые 50 секунд FPS = 25.0 (дельта 0.04с)
        part1 = np.arange(0, 50, 0.2)
        part2 = np.arange(50, 100.04, 0.04)
        self.vfr_timestamps = np.concatenate([part1, part2])
        
        total_frames = len(self.vfr_timestamps)
        duration = self.vfr_timestamps[-1] - self.vfr_timestamps[0]
        
        self.video_info = VideoInfo(
            path=Path("dummy_vfr.asf"),
            input_width=1920,
            input_height=1080,
            fps_nominal=15.0,
            total_frames=total_frames,
            duration_sec=duration,
            timestamps_source="ffprobe packet timestamps",
            timestamps_available=True,
            first_timestamp_sec=float(self.vfr_timestamps[0]),
            last_timestamp_sec=float(self.vfr_timestamps[-1]),
            timestamps_sec=self.vfr_timestamps,
        )
        
        self.data = Data()
        self.data.time = np.linspace(0, 100, 1001)
        self.data.emf = np.linspace(0, 10, 1001)
        self.data.temp = np.linspace(20, 1000, 1001)
        self.data.operator = "Test"
        self.data.sample = "VFR_Sample"

    def test_vfr_native_1to1_alignment(self):
        """Проверяет нативное VFR 1:1 сопоставление физических кадров."""
        timeline = build_timeline_selection(self.data, self.video_info)
        
        self.assertIn(timeline.status, (OverlapStatus.FULL, OverlapStatus.PARTIAL))
        n_kept = len(timeline.kept_timestamps_sec)
        self.assertTrue(n_kept > 0)
        np.testing.assert_allclose(timeline.kept_timestamps_sec, self.vfr_timestamps[:n_kept], atol=1e-5)
        
        # Погрешность привязки кадра к нативным таймстампам ровно 0.0
        frame_matching_err = np.abs(self.vfr_timestamps[timeline.source_frame_indices] - timeline.kept_timestamps_sec).max()
        self.assertEqual(frame_matching_err, 0.0)


if __name__ == "__main__":
    unittest.main()
