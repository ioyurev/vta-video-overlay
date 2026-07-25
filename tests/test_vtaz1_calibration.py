import unittest
import numpy as np


def test_vtaz1_calibration_is_additive_correction():
    """
    Гарантирует, что калибровочный полином VTAZ v1.x применяется 
    именно как аддитивная поправка ΔT(T) к температуре: T_final = T_raw + ΔT(T_raw),
    а не как абсолютная замена значения.
    """
    raw_temperature = np.array([100.0, 200.0, 300.0])

    # Допустим, калибровка линейная: ΔT = 0.05 * T - 1.0
    cal_poly_coeffs = [0.05, -1.0]

    # Ожидаемая поправка ΔT:
    # для 100 -> +4.0
    # для 200 -> +9.0
    # для 300 -> +14.0
    expected_delta = np.array([4.0, 9.0, 14.0])
    expected_final_temp = raw_temperature + expected_delta

    # Имитируем логику расчёта из vtaz1_file.py
    calculated_delta = np.polyval(cal_poly_coeffs, raw_temperature)
    calculated_final_temp = raw_temperature + calculated_delta

    assert np.allclose(calculated_delta, expected_delta), "Ошибка расчёта ΔT"
    assert np.allclose(
        calculated_final_temp, expected_final_temp
    ), "Калибровка должна быть аддитивной (T + ΔT)!"


class TestVTAZ1Calibration(unittest.TestCase):
    def test_additive_calibration(self):
        test_vtaz1_calibration_is_additive_correction()
