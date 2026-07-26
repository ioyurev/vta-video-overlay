import unittest
import numpy as np

from vta_video_overlay.aligned_data import AlignedData, calculate_speed
from vta_video_overlay.data_file import Data


class TestAlignedDataInterpolation(unittest.TestCase):

    def setUp(self):
        self.data = Data()
        self.data.time = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
        self.data.emf = np.array([0.0, 10.0, 20.0, 30.0, 40.0])
        self.data.temp = np.array([100.0, 200.0, 300.0, 400.0, 500.0])

    def test_exact_data_points(self):
        """Если timestamps совпадают с data.time — интерполяция точна."""
        ts = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
        aligned = AlignedData.from_data(ts, self.data)

        assert aligned.emf is not None
        assert aligned.temp is not None
        assert self.data.emf is not None
        assert self.data.temp is not None

        np.testing.assert_allclose(aligned.emf, self.data.emf)
        np.testing.assert_allclose(aligned.temp, self.data.temp)

    def test_midpoint_interpolation(self):
        """Интерполяция в средних точках."""
        ts = np.array([0.5, 1.5, 2.5, 3.5])
        aligned = AlignedData.from_data(ts, self.data)

        assert aligned.emf is not None
        assert aligned.temp is not None

        np.testing.assert_allclose(aligned.emf, [5.0, 15.0, 25.0, 35.0])
        np.testing.assert_allclose(aligned.temp, [150.0, 250.0, 350.0, 450.0])

    def test_out_of_range_clamps(self):
        """np.interp зажимает за пределами диапазона."""
        ts = np.array([-1.0, 5.0])
        aligned = AlignedData.from_data(ts, self.data)

        assert aligned.emf is not None
        self.assertAlmostEqual(aligned.emf[0], 0.0)   # clamped to first
        self.assertAlmostEqual(aligned.emf[1], 40.0)   # clamped to last

    def test_no_temp_means_no_speed(self):
        """Без температуры скорость == None."""
        self.data.temp = None
        ts = np.array([0.0, 1.0, 2.0])
        aligned = AlignedData.from_data(ts, self.data)

        self.assertIsNone(aligned.temp)
        self.assertIsNone(aligned.speed)

    def test_speed_is_computed_when_temp_exists(self):
        ts = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
        aligned = AlignedData.from_data(ts, self.data)

        self.assertIsNotNone(aligned.speed)
        assert aligned.speed is not None
        self.assertEqual(len(aligned.speed), len(ts))

    def test_at_index_returns_correct_values(self):
        ts = np.array([0.0, 1.0, 2.0])
        aligned = AlignedData.from_data(ts, self.data)

        emf, temp, speed = aligned.at_index(0)
        self.assertAlmostEqual(emf, 0.0)
        assert temp is not None
        self.assertAlmostEqual(temp, 100.0)

    def test_single_timestamp(self):
        ts = np.array([2.0])
        aligned = AlignedData.from_data(ts, self.data)

        assert aligned.emf is not None
        self.assertEqual(len(aligned.emf), 1)
        self.assertAlmostEqual(aligned.emf[0], 20.0)


class TestCalculateSpeed(unittest.TestCase):

    def test_constant_temp_zero_speed(self):
        """Постоянная температура → скорость ≈ 0."""
        x = np.linspace(0, 10, 100)
        y = np.full_like(x, 500.0)
        speed = calculate_speed(x, y)

        assert speed is not None
        np.testing.assert_allclose(speed, 0.0, atol=1e-10)

    def test_linear_temp_constant_speed(self):
        """Линейная температура → постоянная скорость."""
        x = np.linspace(0, 10, 1000)
        y = 5.0 * x + 100  # 5 °C/s
        speed = calculate_speed(x, y)

        assert speed is not None
        # Из-за сглаживания на краях будут артефакты — проверяем центр
        center = speed[100:-100]
        np.testing.assert_allclose(center, 5.0, atol=0.5)

    def test_none_returns_none(self):
        x = np.linspace(0, 10, 100)
        self.assertIsNone(calculate_speed(x, None))

    def test_short_array(self):
        x = np.array([0.0])
        y = np.array([100.0])
        speed = calculate_speed(x, y)
        assert speed is not None
        self.assertEqual(len(speed), 1)


if __name__ == "__main__":
    unittest.main()
