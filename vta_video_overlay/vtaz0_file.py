import csv
import json
from io import TextIOWrapper
from pathlib import Path
from typing import TextIO, Tuple
from zipfile import ZIP_DEFLATED, ZipFile

import numpy as np
from data_file import Data
from pydantic import BaseModel, ConfigDict
from PySide6 import QtWidgets

from vta_video_overlay.file_widget_base import FileDataWidgetBase


class VTAZFileWidget(FileDataWidgetBase):
    def __init__(
        self,
        sample: str,
        operator: str,
        path: Path,
        time: np.ndarray,
        emf: np.ndarray,
        temp: np.ndarray | None,
        vtaz_version: str,
        has_calibration: bool,
        calibration_coeffs: tuple | None = None,
    ):
        self.vtaz_version = vtaz_version
        self.has_calibration = has_calibration
        self.calibration_coeffs = calibration_coeffs
        super().__init__(sample, operator, path, time, emf, temp)

    def add_specific_content(self, layout: QtWidgets.QVBoxLayout):
        """Add VTAZ-specific content"""
        # Version info
        version_group = QtWidgets.QGroupBox("File Information")
        version_layout = QtWidgets.QFormLayout()
        version_layout.addRow("Version:", QtWidgets.QLabel(self.vtaz_version))
        version_layout.addRow(
            "Calibration:",
            QtWidgets.QLabel("Available" if self.has_calibration else "Not available"),
        )
        version_group.setLayout(version_layout)
        layout.addWidget(version_group)

        # Calibration coefficients if available
        if self.has_calibration and self.calibration_coeffs:
            coeffs_group = QtWidgets.QGroupBox("Calibration Coefficients")
            coeffs_layout = QtWidgets.QFormLayout()
            coeffs_layout.addRow(
                "c3:", QtWidgets.QLabel(str(self.calibration_coeffs[0]))
            )
            coeffs_layout.addRow(
                "c2:", QtWidgets.QLabel(str(self.calibration_coeffs[1]))
            )
            coeffs_layout.addRow(
                "c1:", QtWidgets.QLabel(str(self.calibration_coeffs[2]))
            )
            coeffs_layout.addRow(
                "c0:", QtWidgets.QLabel(str(self.calibration_coeffs[3]))
            )
            coeffs_group.setLayout(coeffs_layout)
            layout.addWidget(coeffs_group)


class Metadata(BaseModel):
    sample: str
    operator: str
    vtaz_version: str = "0.0"


class VTAZ0File(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    path: Path
    metadata: Metadata
    time: np.ndarray
    emf: np.ndarray
    temp: np.ndarray | None
    has_cal: bool
    coeff: tuple[float, float, float, float] | None

    @classmethod
    def load(cls, path: Path):
        with ZipFile(path, "r", ZIP_DEFLATED) as zipf:
            metadata_str = zipf.read("metadata.json").decode("utf-8")
            metadata = Metadata.model_validate_json(metadata_str)
            with zipf.open("data_input.csv", "r") as byte_f:
                text_f = TextIOWrapper(buffer=byte_f, encoding="utf-8")
                time, emf = read_csv(f=text_f)

            has_cal = "calibration.json" in zipf.namelist()
            if has_cal:
                with zipf.open("calibration.json", "r") as byte_f:
                    text_f = TextIOWrapper(buffer=byte_f, encoding="utf-8")
                    content = json.load(text_f)
                    coeff = (content["c3"], content["c2"], content["c1"], content["c0"])
                    np_coeff = np.array(coeff, dtype=float)
                    xn = np.poly1d(np_coeff)
                    temp = xn(emf)
            else:
                coeff = None
                temp = None

        return cls(
            metadata=metadata,
            time=time,
            emf=emf,
            temp=temp,
            path=path,
            has_cal=has_cal,
            coeff=coeff,
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

    def create_widget(self):
        """Create widget for displaying VTAZ file information"""
        return VTAZFileWidget(
            sample=self.metadata.sample,
            operator=self.metadata.operator,
            path=self.path,
            time=self.time,
            emf=self.emf,
            temp=self.temp,
            vtaz_version=self.metadata.vtaz_version,
            has_calibration=self.has_cal,
            calibration_coeffs=self.coeff,
        )


def read_csv(f: TextIO) -> Tuple[np.ndarray, np.ndarray]:
    # Читаем всё содержимое и разделяем
    content = f.read()
    lines = [line.removesuffix(";") for line in content.strip().split()]

    # Парсим CSV
    reader = csv.reader(lines)
    next(reader)  # Пропускаем заголовок

    x_list, y_list = [], []
    for row in reader:
        if len(row) >= 2:
            x_list.append(float(row[0]))
            y_list.append(float(row[1]))

    return np.array(x_list), np.array(y_list)
