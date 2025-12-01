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
            sample=sample, operator=operator, time=time, emf=emf, temp=temp, coeff=coeff
        )

    def to_data(self) -> Data:
        data = Data()
        data.sample = self.sample
        data.operator = self.operator
        data.time = self.time
        data.emf = self.emf
        data.temp = self.temp
        return data

    def create_widget(self, path: Path):
        """Create widget for displaying TDA file information"""
        return TDAFileWidget(
            sample=self.sample,
            operator=self.operator,
            path=path,
            time=self.time,
            emf=self.emf,
            temp=self.temp,
            coefficients=self.coeff,
        )


def parse_lines(lines: list[str]) -> tuple[list[str], str, str, list[str]]:
    for index, line in enumerate(lines):
        if line[0] == "<":
            if line.startswith("<NAME>"):
                sample_name = line[7 : len(line) - 1]
            elif line.startswith("<AUTOR>"):
                operator = line[8 : len(line) - 1]
            elif line.startswith("<FORMULE>"):
                coeff = line[12 : len(line) - 1].split(sep=" ")
            continue
        else:
            start_index = index
            break
    lines_data = lines[start_index:-1]
    return lines_data, sample_name, operator, coeff
