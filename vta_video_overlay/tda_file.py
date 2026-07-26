"""
Module for processing VPTAnalyzer's .tda data files

Key Features:
- Parsing specialized .tda file format containing measurements data
- Extraction of measurement metadata (operator, sample name)
- Processing of polynomial coefficients for temperature calibration
- Conversion of raw measurement data into numerical arrays

File Format Specifications:
- Windows-1251 encoding with comma decimal separators
- XML-like header section containing metadata
- Space-separated numerical data table
- Timestamps stored in fractional days requiring conversion to seconds

Typical Usage Example:
    tda_file = TDAFile.load(Path("measurement.tda"))

Data Handling:
- Automatic time conversion from days to seconds
- Locale-aware number parsing (Russian decimal format)
- Polynomial coefficient normalization
"""

from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict
from PySide6 import QtWidgets

from vta_video_overlay.data_file import Data
from vta_video_overlay.file_widget_base import FileDataWidgetBase
from vta_video_overlay.info_models import MeasurementInfo
from vta_video_overlay.measurement_helpers import build_data, compute_ranges
from vta_video_overlay.tda_headers import Headers


class TDAFileWidget(FileDataWidgetBase):
    def __init__(
        self,
        sample: str,
        operator: str,
        path: Path,
        time: np.ndarray,
        emf: np.ndarray,
        temp: np.ndarray | None,
        coefficients: list[str],
    ):
        self.coefficients = coefficients
        super().__init__(sample, operator, path, time, emf, temp)

    def add_specific_content(self, layout: QtWidgets.QVBoxLayout):
        """Add TDA-specific content"""
        coeffs_group = QtWidgets.QGroupBox("Polynomial Coefficients")
        coeffs_layout = QtWidgets.QVBoxLayout()

        coeffs_text = QtWidgets.QTextEdit()
        coeffs_text.setPlainText(", ".join(self.coefficients))
        coeffs_text.setMaximumHeight(60)
        coeffs_text.setReadOnly(True)
        coeffs_layout.addWidget(coeffs_text)

        coeffs_group.setLayout(coeffs_layout)
        layout.addWidget(coeffs_group)


class TDAFile(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    path: Path
    sample: str
    operator: str
    time: np.ndarray
    emf: np.ndarray
    temp: np.ndarray | None
    coeff: list[str]

    @classmethod
    def load(cls, path: Path):
        with open(file=path, mode="r", encoding="cp1251") as f:
            lines_raw = f.readlines()
        lines_data, sample, operator, coeff = parse_lines(lines=lines_raw)
        buffer = StringIO("".join(lines_data))
        df = pd.read_csv(
            buffer,
            sep=" ",
            header=None,
            usecols=[0, 1],
            decimal=",",
            names=[Headers.EMF, Headers.TIME_RAW],
        )
        # VPTAnalyzer stores time values in... days? Therefore, the time value
        # is multiplied by 86,400 to convert it to seconds (24h * 60m * 60s = 86,400 seconds/day)
        df[Headers.TIME] = df[Headers.TIME_RAW] * 86400
        for index, item in enumerate(coeff):
            coeff[index] = item.replace(",", ".")
        time = df[Headers.TIME].to_numpy()
        emf = df[Headers.EMF].to_numpy()
        # Вычисляем температуру из коэффициентов и ЭДС
        try:
            np_coeff = np.array(coeff, dtype=float)
            xn = np.poly1d(np_coeff)
            temp = xn(emf)
        except Exception:
            temp = None

        return cls(
            path=path,
            sample=sample,
            operator=operator,
            time=time,
            emf=emf,
            temp=temp,
            coeff=coeff,
        )

    def to_data(self) -> Data:
        return build_data(
            path=self.path,
            operator=self.operator,
            sample=self.sample,
            time=self.time,
            emf=self.emf,
            temp=self.temp,
        )

    def to_info(self) -> MeasurementInfo:
        stats = compute_ranges(self.time, self.emf, self.temp)

        return MeasurementInfo(
            source_format="TDA",
            version="legacy",
            path=self.path,
            sample=self.sample,
            operator=self.operator,
            points=len(self.time),
            t_min_sec=stats["t_min"],
            t_max_sec=stats["t_max"],
            duration_sec=stats["t_max"] - stats["t_min"],
            emf_min=stats["emf_min"],
            emf_max=stats["emf_max"],
            temp_available=self.temp is not None,
            temp_min=stats["temp_min"],
            temp_max=stats["temp_max"],
            calibration_available=self.temp is not None and bool(self.coeff),
            calibration_type="polynomial" if self.coeff else None,
            calibration_semantics="EMF → T",
            calibration_coeffs_text=", ".join(self.coeff) if self.coeff else None,
        )

    def create_widget(self, path: Path | None = None) -> TDAFileWidget:
        """Create widget for displaying TDA file information"""
        target_path = path if path is not None else self.path
        return TDAFileWidget(
            sample=self.sample,
            operator=self.operator,
            path=target_path,
            time=self.time,
            emf=self.emf,
            temp=self.temp,
            coefficients=self.coeff,
        )


def parse_lines(lines: list[str]) -> tuple[list[str], str, str, list[str]]:
    sample_name: str = ""
    operator: str = ""
    coeff: list[str] = []
    start_index: int = len(lines)

    for index, line in enumerate(lines):
        stripped = line.rstrip("\n\r")
        if not stripped:
            continue
        if stripped[0] == "<":
            if stripped.startswith("<NAME>"):
                sample_name = stripped[7:]
            elif stripped.startswith("<AUTOR>"):
                operator = stripped[8:]
            elif stripped.startswith("<FORMULE>"):
                coeff = stripped[12:].split()
        else:
            start_index = index
            break

    lines_data = lines[start_index:-1] if start_index < len(lines) else []
    return lines_data, sample_name, operator, coeff
