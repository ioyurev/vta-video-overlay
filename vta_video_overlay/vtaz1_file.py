"""
Module for processing new version .vtaz data files (version 1.0+)

Key Features:
- Full temperature processing chain with thermocouple compensation
- Cold junction compensation support
- Polynomial conversion using 8th degree thermocouple coefficients
- ZIP-based archive format support
- Class-based architecture with VTAZ1File model
- Data conversion support via to_data method

File Format Specifications (v1.0+):
- metadata.json: sample, operator, vtaz_version, created_at
- data_input.csv: time-EMF measurements
- calibration.json: full calibration data (stores ADDITIVE correction ΔT(T), not absolute T)
- thermocouple.json: thermocouple coefficients
- cjc.json: cold junction compensation data

Temperature Reconstruction Formula:
    1. E_comp  = E_measured + E_cold
    2. T_raw   = polyval(thermocouple_coeffs, E_comp)
    3. ΔT      = polyval(calibration_coeffs, T_raw)
    4. T_final = T_raw + ΔT  <-- Additive correction applied here

Typical Usage Example:
    vtaz_file = VTAZ1File.load(Path("measurement.vtaz"))
    data = vtaz_file.to_data()
"""

import json
from io import TextIOWrapper
from pathlib import Path
from typing import Optional
from zipfile import ZIP_DEFLATED, ZipFile

import numpy as np
from pydantic import BaseModel, ConfigDict
from PySide6 import QtWidgets

from vta_video_overlay.data_file import Data
from vta_video_overlay.file_widget_base import FileDataWidgetBase
from vta_video_overlay.info_models import MeasurementInfo
from vta_video_overlay.vtaz0_file import Metadata, read_csv


class VTAZ1FileWidget(FileDataWidgetBase):
    def __init__(
        self,
        sample: str,
        operator: str,
        path: Path,
        time: np.ndarray,
        emf: np.ndarray,
        temp: np.ndarray | None,
        vtaz_version: str,
        thermocouple_coeffs: list[float] | None = None,
        cjc_data: dict | None = None,
        calibration_coeffs: list[float] | None = None,
    ):
        self.vtaz_version = vtaz_version
        self.thermocouple_coeffs = thermocouple_coeffs
        self.cjc_data = cjc_data
        self.calibration_coeffs = calibration_coeffs
        super().__init__(sample, operator, path, time, emf, temp)

    def add_specific_content(self, layout: QtWidgets.QVBoxLayout):
        """Add VTAZ1-specific content"""
        # Version info
        version_group = QtWidgets.QGroupBox("File Information")
        version_layout = QtWidgets.QFormLayout()
        version_layout.addRow("Version:", QtWidgets.QLabel(self.vtaz_version))
        version_group.setLayout(version_layout)
        layout.addWidget(version_group)

        # Thermocouple coefficients if available
        if self.thermocouple_coeffs:
            coeffs_group = QtWidgets.QGroupBox("Thermocouple Coefficients")
            coeffs_layout = QtWidgets.QVBoxLayout()
            coeffs_text = QtWidgets.QTextEdit()
            coeffs_text.setPlainText(str(self.thermocouple_coeffs))
            coeffs_text.setMaximumHeight(80)
            coeffs_text.setReadOnly(True)
            coeffs_layout.addWidget(coeffs_text)
            coeffs_group.setLayout(coeffs_layout)
            layout.addWidget(coeffs_group)

        # Calibration coefficients if available
        if self.calibration_coeffs:
            cal_group = QtWidgets.QGroupBox("Calibration Coefficients")
            cal_layout = QtWidgets.QVBoxLayout()
            cal_text = QtWidgets.QTextEdit()
            cal_text.setPlainText(str(self.calibration_coeffs))
            cal_text.setMaximumHeight(60)
            cal_text.setReadOnly(True)
            cal_layout.addWidget(cal_text)
            cal_group.setLayout(cal_layout)
            layout.addWidget(cal_group)

        # CJC data if available
        if self.cjc_data:
            cjc_group = QtWidgets.QGroupBox("Cold Junction Compensation")
            cjc_layout = QtWidgets.QFormLayout()
            for key, value in self.cjc_data.items():
                cjc_layout.addRow(key + ":", QtWidgets.QLabel(str(value)))
            cjc_group.setLayout(cjc_layout)
            layout.addWidget(cjc_group)


class VTAZ1File(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    path: Path
    metadata: Metadata
    time: np.ndarray
    emf: np.ndarray
    temp: Optional[
        np.ndarray
    ]  # Температура может быть None если калибровка отсутствует
    calibration_coeffs: list[float] | None
    calibration_type: str | None = None
    thermocouple_coeffs: list[float] | None
    cjc_data: dict | None

    @classmethod
    def load(cls, path: Path):
        with ZipFile(path, "r", ZIP_DEFLATED) as zipf:
            # Загружаем метаданные
            metadata_str = zipf.read("metadata.json").decode("utf-8")
            metadata = Metadata.model_validate_json(metadata_str)

            # Загружаем данные
            with zipf.open("data_input.csv", "r") as byte_f:
                text_f = TextIOWrapper(buffer=byte_f, encoding="utf-8")
                time, emf = read_csv(f=text_f)

            # Загружаем калибровку
            with zipf.open("calibration.json", "r") as byte_f:
                text_f = TextIOWrapper(buffer=byte_f, encoding="utf-8")
                calibration_data = json.load(text_f)
                
                # Получаем коэффициенты и тип калибровки
                calibration_coeffs = calibration_data.get("coefficients")
                calibration_type = calibration_data.get("calibration_type", "linear")

                if calibration_coeffs is None:
                    raise ValueError(
                        "Calibration coefficients cannot be None. Please provide valid calibration coefficients."
                    )

            # Загружаем коэффициенты термопары
            with zipf.open("thermocouple.json", "r") as byte_f:
                text_f = TextIOWrapper(buffer=byte_f, encoding="utf-8")
                thermocouple_data = json.load(text_f)
                thermocouple_coeffs = thermocouple_data["thermocouple_coefficients"]

            # Загружаем данные холодного спая
            with zipf.open("cjc.json", "r") as byte_f:
                text_f = TextIOWrapper(buffer=byte_f, encoding="utf-8")
                cjc_data = json.load(text_f)

            # --- РАСЧЕТ ТЕМПЕРАТУРЫ ---

            # 1. Компенсация холодного спая
            e_cold = cjc_data.get("e_cold", 0.0)

            # print(f"{e_cold=}")
            compensated_emf = emf + e_cold

            # print(f"{compensated_emf=}")

            # 2. Преобразование ЭДС в сырую температуру
            # Коэффициенты термопары в JSON: [c0, c1, ..., c8] (от младшей степени к старшей)
            # np.polyval требует [c8, ..., c0] (от старшей к младшей), поэтому разворачиваем [::-1]
            raw_temperature = np.polyval(thermocouple_coeffs[::-1], compensated_emf)

            # 3. Применение калибровки
            # IMPORTANT CONTRACT:
            # calibration_coeffs in VTAZ v1.x represent an additive correction polynomial ΔT(T),
            # NOT the absolute calibrated temperature. We must add ΔT to raw_temperature.
            calc_coeffs = list(calibration_coeffs)
            while len(calc_coeffs) < 3:
                calc_coeffs.append(0.0)

            if calibration_type == "linear":
                # Берем [a, b] для ax + b
                cal_poly_coeffs = calc_coeffs[:2]
            else:  # quadratic
                # Берем [a, b, c] для ax^2 + bx + c
                cal_poly_coeffs = calc_coeffs[:3]

            temp_correction_delta = np.polyval(cal_poly_coeffs, raw_temperature)
            final_temperature = raw_temperature + temp_correction_delta

        return cls(
            metadata=metadata,
            time=time,
            emf=emf,
            temp=final_temperature,
            path=path,
            calibration_coeffs=calibration_coeffs,
            calibration_type=calibration_type,
            thermocouple_coeffs=thermocouple_coeffs,
            cjc_data=cjc_data,
        )

    def to_data(self) -> Data:
        data = Data()
        data.path = self.path
        data.operator = self.metadata.operator
        data.sample = self.metadata.sample
        data.time = self.time
        data.emf = self.emf
        data.temp = self.temp

        return data

    def to_info(self) -> MeasurementInfo:
        t_min = float(self.time[0]) if len(self.time) else 0.0
        t_max = float(self.time[-1]) if len(self.time) else 0.0
        emf_min = float(self.emf.min()) if len(self.emf) else None
        emf_max = float(self.emf.max()) if len(self.emf) else None
        temp_min = (
            float(self.temp.min())
            if self.temp is not None and len(self.temp)
            else None
        )
        temp_max = (
            float(self.temp.max())
            if self.temp is not None and len(self.temp)
            else None
        )

        return MeasurementInfo(
            source_format="VTAZ",
            version=self.metadata.vtaz_version,
            path=self.path,
            sample=self.metadata.sample,
            operator=self.metadata.operator,
            points=len(self.time),
            t_min_sec=t_min,
            t_max_sec=t_max,
            duration_sec=t_max - t_min,
            emf_min=emf_min,
            emf_max=emf_max,
            temp_available=self.temp is not None,
            temp_min=temp_min,
            temp_max=temp_max,
            calibration_available=self.calibration_coeffs is not None,
            calibration_type=self.calibration_type,
            calibration_semantics="ΔT(T), additive correction",
            calibration_coeffs_text=str(self.calibration_coeffs)
            if self.calibration_coeffs
            else None,
            thermocouple_coeffs_text=str(self.thermocouple_coeffs)
            if self.thermocouple_coeffs
            else None,
            cjc_text=str(self.cjc_data) if self.cjc_data else None,
        )

    def create_widget(self):
        """Create widget for displaying VTAZ1 file information"""
        return VTAZ1FileWidget(
            sample=self.metadata.sample,
            operator=self.metadata.operator,
            path=self.path,
            time=self.time,
            emf=self.emf,
            temp=self.temp,
            vtaz_version=self.metadata.vtaz_version,
            thermocouple_coeffs=self.thermocouple_coeffs,
            cjc_data=self.cjc_data,
            calibration_coeffs=self.calibration_coeffs,
        )