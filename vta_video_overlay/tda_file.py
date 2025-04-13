"""
TDA file parser and scientific data processor

Key Responsibilities:
- Parse VPTAnalyzer's proprietary .tda sensor data format
- Handle scientific notation and locale-specific number formatting
- Manage polynomial temperature calibration formulas
- Generate Excel reports with interactive charts and metadata
- Maintain time synchronization between sensor data and video

File Format Specifications:
- Custom ASCII format with XML-like metadata headers
- Tabular data in space-separated columns
- Windows-1251 encoding with comma decimal separators
- Contains:
  - Measurement metadata (operator, sample, timestamps)
  - Raw EMF (electromotive force) measurements
  - Polynomial coefficients for temperature conversion

Processing Flow:
1. Metadata extraction from header lines
2. Numeric data parsing with locale adaptation
3. Timebase conversion (days to seconds)
4. Temperature polynomial application
5. Excel workbook creation with embedded charts
"""

from io import StringIO
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
from loguru import logger as log
from PySide6 import QtCore


class Headers:
    EMF: Final = "EMF, mV"
    TIME_RAW: Final = "Time, s/86400"
    TIME: Final = "Time, s"
    TEMP: Final = "Temperature, °C"


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


class Data(QtCore.QObject):
    operator: str
    sample: str
    coeff: list[str]

    def __init__(self, path: Path, temp_enabled=True) -> None:
        super().__init__()
        self.path = path
        with open(file=path, mode="r", encoding="cp1251") as f:
            lines_raw = f.readlines()
        lines_data, self.sample, self.operator, self.coeff = parse_lines(
            lines=lines_raw
        )
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
        for index, item in enumerate(self.coeff):
            self.coeff[index] = item.replace(",", ".")
        self.data_time = df[Headers.TIME].to_numpy()
        self.data_emf = df[Headers.EMF].to_numpy()
        self.temp_enabled = temp_enabled
        self.recalc_temp()

    def recalc_temp(self):
        if self.temp_enabled:
            np_coeff = np.array(self.coeff, dtype=float)
            xn = np.poly1d(np_coeff)
            self.data_temp = xn(self.data_emf)

    def to_excel(self, path: Path):
        log.info(self.tr("Saving .xlsx: {path}").format(path=path))
        df = pd.DataFrame()
        df[Headers.TIME] = self.data_time.round(3)
        df[Headers.EMF] = self.data_emf.round(3)
        if self.temp_enabled:
            df[Headers.TEMP] = self.data_temp.round()
        writer = pd.ExcelWriter(path, engine="xlsxwriter")
        sheet_name = "Sheet1"
        df.to_excel(excel_writer=writer, index=False, sheet_name=sheet_name)
        workbook = writer.book
        worksheet = writer.sheets[sheet_name]
        chart = workbook.add_chart({"type": "scatter", "subtype": "straight"})
        if self.temp_enabled:
            column = "C"
            yaxis = Headers.TEMP
        else:
            column = "B"
            yaxis = Headers.EMF
        series_data = {
            "categories": f"={sheet_name}!$A:$A",
            "values": f"={sheet_name}!${column}:${column}",
        }
        chart.add_series(series_data)
        chart.set_legend({"position": "none"})
        chart.set_x_axis({"name": Headers.TIME})
        chart.set_y_axis({"name": yaxis})
        worksheet.insert_chart("E2", chart)
        workbook.close()
