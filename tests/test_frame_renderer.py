import unittest
import numpy as np
from unittest.mock import MagicMock

from vta_video_overlay.data_file import Data
from vta_video_overlay.frame_renderer import FrameRenderer
from vta_video_overlay.video_context import VideoContext


class TestFrameRendererIndexing(unittest.TestCase):
    """Проверяет что FrameRenderer использует правильные данные для каждого кадра."""

    def setUp(self):
        self.data = Data()
        self.data.time = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
        self.data.emf = np.array([0.0, 10.0, 20.0, 30.0, 40.0])
        self.data.temp = np.array([100.0, 200.0, 300.0, 400.0, 500.0])
        self.data.operator = "Op"
        self.data.sample = "Smp"

        self.timestamps = np.array([0.0, 1.0, 2.0, 3.0, 4.0])

        self.mock_ctx = MagicMock(spec=VideoContext)
        self.mock_ctx.fps = 1.0
        self.mock_ctx.total_frames = 5
        self.mock_ctx.width = 640
        self.mock_ctx.height = 480

    def test_aligned_data_matches_timestamps(self):
        """AlignedData внутри renderer соответствует переданным timestamps."""
        renderer = FrameRenderer(
            video_ctx=self.mock_ctx,
            data=self.data,
            timestamps=self.timestamps,
            graph_enabled=False,
        )

        assert renderer.aligned.emf is not None
        assert renderer.aligned.temp is not None
        assert self.data.emf is not None
        assert self.data.temp is not None

        np.testing.assert_allclose(renderer.aligned.emf, self.data.emf)
        np.testing.assert_allclose(renderer.aligned.temp, self.data.temp)

    def test_render_overlay_uses_correct_index(self):
        """render_overlay(img, frame_index=2) берёт данные для timestamps[2]."""
        renderer = FrameRenderer(
            video_ctx=self.mock_ctx,
            data=self.data,
            timestamps=self.timestamps,
            graph_enabled=False,
        )

        img = np.zeros((480, 640, 3), dtype=np.uint8)
        frame = renderer.render_overlay(img, 2)

        self.assertIsNotNone(frame)
        # emf при idx=2 должна быть 20.0
        emf, temp, speed = renderer.aligned.at_index(2)
        self.assertAlmostEqual(emf, 20.0)
        assert temp is not None
        self.assertAlmostEqual(temp, 300.0)


if __name__ == "__main__":
    unittest.main()
