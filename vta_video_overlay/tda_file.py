"""
TDA file parsing and data management

Key Responsibilities:
- Parse VPTAnalyzer (.tda) file format
- Handle sensor data extraction and temperature calibration
- Manage polynomial coefficient processing for temperature conversion
- Generate Excel reports with formatted data and charts

Main Components:
- Data: Core data container class implementing:
  - TDA file parsing and metadata extraction
  - Temperature calculation via polynomial coefficients
  - Excel report generation with embedded charts
- Headers: Column name definitions for data structuring

Dependencies:
- pandas: DataFrame management for Excel export
- numpy: Numerical array operations
- pathlib: Cross-platform file path handling
- openpyxl: Excel workbook/chart generation
- PySide6.QtCore: Translation support

File Format Handling:
- Processes custom TDA format containing:
  - Metadata headers (XML-like tags)
  - Tabular sensor measurements
  - Calibration coefficients

Processing Flow:
1. Parse metadata headers
2. Extract numerical measurements
3. Apply temperature calibration
4. Generate structured DataFrame
5. Export to formatted Excel workbook
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
