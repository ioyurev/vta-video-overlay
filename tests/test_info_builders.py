import unittest
import numpy as np
from pathlib import Path

from vta_video_overlay.data_file import Data
from vta_video_overlay.enums import OverlapStatus
from vta_video_overlay.info_builders import (
    build_aligned_info,
    build_timeline_selection,
    update_video_info_with_timeline,
)
from vta_video_overlay.info_models import VideoInfo


class TestUpdateVideoInfoWithTimeline(unittest.TestCase):

    def test_none_timeline_clears_used_fields(self):
        ts = np.linspace(0, 100, 500)
        video = VideoInfo(
            path=Path("t.mp4"), input_width=640, input_height=480,
            fps_nominal=25.0, total_frames=500, duration_sec=100.0,
            timestamps_source="test", timestamps_available=True,
            first_timestamp_sec=0.0, last_timestamp_sec=100.0,
            timestamps_sec=ts,
        )
        data = Data()
        data.time = np.linspace(200, 300, 100)
        data.emf = np.zeros(100)

        tl = build_timeline_selection(data, video)
        updated = update_video_info_with_timeline(video, tl)

        self.assertIsNone(updated.used_start_sec)
        self.assertIsNone(updated.used_end_sec)

    def test_partial_timeline_sets_used_fields(self):
        ts = np.linspace(0, 100, 500)
        video = VideoInfo(
            path=Path("t.mp4"), input_width=640, input_height=480,
            fps_nominal=25.0, total_frames=500, duration_sec=100.0,
            timestamps_source="test", timestamps_available=True,
            first_timestamp_sec=0.0, last_timestamp_sec=100.0,
            timestamps_sec=ts,
        )
        data = Data()
        data.time = np.linspace(30, 70, 500)
        data.emf = np.zeros(500)
        data.temp = np.zeros(500)

        tl = build_timeline_selection(data, video)
        updated = update_video_info_with_timeline(video, tl)

        self.assertIsNotNone(updated.used_start_sec)
        self.assertIsNotNone(updated.used_end_sec)
        assert updated.used_start_sec is not None
        assert updated.used_end_sec is not None
        self.assertAlmostEqual(updated.used_start_sec, 30.0, places=0)
        self.assertAlmostEqual(updated.used_end_sec, 70.0, places=0)


class TestBuildAlignedInfo(unittest.TestCase):

    def test_none_timeline_gives_empty_aligned_info(self):
        data = Data()
        ts = np.linspace(0, 100, 500)
        video = VideoInfo(
            path=Path("t.mp4"), input_width=640, input_height=480,
            fps_nominal=25.0, total_frames=500, duration_sec=100.0,
            timestamps_source="test", timestamps_available=True,
            first_timestamp_sec=0.0, last_timestamp_sec=100.0,
            timestamps_sec=ts,
        )
        tl = build_timeline_selection(data, video)
        info = build_aligned_info(data, video, tl)

        self.assertEqual(info.points, 0)
        self.assertIs(info.overlap_status, OverlapStatus.NONE)

    def test_valid_timeline_gives_valid_aligned_info(self):
        data = Data()
        data.time = np.linspace(0, 100, 1000)
        data.emf = np.zeros(1000)
        data.temp = np.linspace(20, 500, 1000)

        ts = np.linspace(0, 100, 500)
        video = VideoInfo(
            path=Path("t.mp4"), input_width=640, input_height=480,
            fps_nominal=25.0, total_frames=500, duration_sec=100.0,
            timestamps_source="test", timestamps_available=True,
            first_timestamp_sec=0.0, last_timestamp_sec=100.0,
            timestamps_sec=ts,
        )
        tl = build_timeline_selection(data, video)
        info = build_aligned_info(data, video, tl)

        self.assertEqual(info.points, 500)
        self.assertTrue(info.temp_available)
        self.assertTrue(info.speed_available)
        self.assertIsNotNone(info.real_fps)
        assert info.real_fps is not None
        self.assertGreater(info.real_fps, 0)


if __name__ == "__main__":
    unittest.main()
