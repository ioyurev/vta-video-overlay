import unittest
import numpy as np
from pathlib import Path

from vta_video_overlay.data_file import Data
from vta_video_overlay.enums import OverlapStatus
from vta_video_overlay.info_builders import build_timeline_selection
from vta_video_overlay.info_models import VideoInfo


def random_timeline_test(seed: int):
    """Генерирует случайную пару (data, video) и проверяет инварианты."""
    rng = np.random.RandomState(seed)

    data_start = rng.uniform(-100, 200)
    data_end = data_start + rng.uniform(1, 200)
    n_data = rng.randint(10, 2000)

    video_start = rng.uniform(-100, 200)
    video_end = video_start + rng.uniform(1, 200)
    n_video = rng.randint(10, 2000)

    data = Data()
    data.time = np.linspace(data_start, data_end, n_data)
    data.emf = rng.randn(n_data)
    data.temp = rng.randn(n_data) * 100 + 500

    video_ts = np.sort(rng.uniform(video_start, video_end, n_video))

    video_info = VideoInfo(
        path=Path("rand.mp4"),
        input_width=640,
        input_height=480,
        fps_nominal=25.0,
        total_frames=n_video,
        duration_sec=float(video_end - video_start),
        timestamps_source="random",
        timestamps_available=True,
        first_timestamp_sec=float(video_ts[0]),
        last_timestamp_sec=float(video_ts[-1]),
        timestamps_sec=video_ts,
    )

    tl = build_timeline_selection(data, video_info)

    # --- ИНВАРИАНТЫ ---

    # 1. kept_frames == len(source_frame_indices) == len(kept_timestamps_sec)
    assert tl.kept_frames == len(tl.source_frame_indices), f"seed={seed}"
    assert tl.kept_frames == len(tl.kept_timestamps_sec), f"seed={seed}"

    # 2. Все индексы валидны
    if tl.kept_frames > 0:
        assert np.all(tl.source_frame_indices >= 0), f"seed={seed}"
        assert np.all(tl.source_frame_indices < n_video), f"seed={seed}"

    # 3. kept_timestamps == video_ts[source_frame_indices]
    if tl.kept_frames > 0:
        expected = video_ts[tl.source_frame_indices]
        np.testing.assert_array_almost_equal(
            tl.kept_timestamps_sec, expected, decimal=10,
            err_msg=f"seed={seed}"
        )

    # 4. source_frame_indices строго возрастают
    if tl.kept_frames > 1:
        assert np.all(np.diff(tl.source_frame_indices) > 0), f"seed={seed}: not sorted"

    # 5. Если NONE — нет кадров
    if tl.status is OverlapStatus.NONE:
        assert tl.kept_frames == 0, f"seed={seed}"

    # 6. Если FULL — нет обрезки
    if tl.status is OverlapStatus.FULL:
        assert tl.trimmed_start_frames == 0, f"seed={seed}"
        assert tl.trimmed_end_frames == 0, f"seed={seed}"

    # 7. overlap_duration >= 0
    assert tl.overlap_duration_sec >= 0, f"seed={seed}"

    # 8. Все kept_timestamps в пределах [overlap_start, overlap_end]
    if tl.kept_frames > 0:
        assert tl.kept_timestamps_sec[0] >= tl.overlap_start_sec - 1e-9, f"seed={seed}"
        assert tl.kept_timestamps_sec[-1] <= tl.overlap_end_sec + 1e-9, f"seed={seed}"


class TestTimelineProperties(unittest.TestCase):

    def test_1000_random_seeds(self):
        """Запускает 1000 случайных конфигураций и проверяет инварианты."""
        for seed in range(1000):
            with self.subTest(seed=seed):
                random_timeline_test(seed)


if __name__ == "__main__":
    unittest.main()
