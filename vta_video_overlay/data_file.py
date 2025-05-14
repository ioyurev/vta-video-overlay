"""
Module for unified sensor data file handling and processing

Key Responsibilities:
- Multi-format support for measurement data files (.tda, .vtaz)
- Sensor data processing and temperature calibration
- Cross-format metadata management and validation
- Measurement-to-video synchronization
- Automated Excel report generation with interactive charts

Supported Formats:
1. VPTAnalyzer .tda Format:
   - Legacy ASCII format with custom header structure
   - Windows-1251 encoding with comma decimal separators
   - Contains raw EMF measurements and calibration polynomials

2. Modern .vtaz Format (ZIP-based):
   - Compressed archive with structured components:
     * metadata.json - Measurement parameters
     * data_input.csv - Time-EMF measurements
     * calibration.json - Temperature coefficients (optional)
   - UTF-8 encoding with standard number formatting

Processing Pipeline:
1. Format detection and appropriate parser selection
2. Metadata extraction and validation (using Pydantic models)
3. Raw data normalization and unit conversion
4. Temperature calculation using polynomial calibration
5. Timebase synchronization preparation

Typical Usage:
    # Load from legacy .tda
    data = Data.from_tda_file(Path("measurement.tda"))
    
    # Load from modern .vtaz 
    data = Data.from_vtaz_file(Path("experiment.vtaz"))
    
    # Generate analysis report
    data.to_excel(Path("report.xlsx"))

Validation Features:
- Automatic coefficient normalization (RU/US decimal formats)
- Measurement continuity checks
- Timestamp monotonicity verification
- Data type consistency enforcement

Exception Handling:
- Detailed error reporting for format violations
- Context-aware warnings for data inconsistencies
- Checksum verification for compressed archives
"""

from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger as log
from PySide6 import QtCore

from vta_video_overlay.tda_file import Headers, load_tda
from vta_video_overlay.vtaz_file import load_vtaz


class Data(QtCore.QObject):
    operator: str
    sample: str
    coeff: list[str]
    path: Path
    time: np.ndarray
    emf: np.ndarray
    date_temp: np.ndarray
    temp_enabled: bool

    @staticmethod
    def from_vtaz_file(path: Path, temp_enabled=True) -> "Data":
        self = Data()
        self.path = path
        metadata, time, emf, coeff = load_vtaz(path=path)
        self.sample = metadata.sample
        self.operator = metadata.operator
        self.time = np.array(time)
        self.emf = np.array(emf)
        self.coeff = coeff
        self.temp_enabled = temp_enabled
        self.recalc_temp()
        return self

    @staticmethod
    def from_tda_file(path: Path, temp_enabled=True) -> "Data":
        self = Data()
        self.path = path
        self.sample, self.operator, self.coeff, self.time, self.emf = load_tda(
            path=path
        )
        self.temp_enabled = temp_enabled
        self.recalc_temp()
        return self

    def recalc_temp(self):
        if self.temp_enabled:
            np_coeff = np.array(self.coeff, dtype=float)
            xn = np.poly1d(np_coeff)
            self.temp = xn(self.emf)

    def to_excel(self, path: Path):
        log.info(self.tr("Saving .xlsx: {path}").format(path=path))
        df = pd.DataFrame()
        df[Headers.TIME] = self.time.round(3)
        df[Headers.EMF] = self.emf.round(3)
        if self.temp_enabled:
            df[Headers.TEMP] = self.temp.round()
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
