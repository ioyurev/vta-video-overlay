import pandas as pd
import numpy as np
from pathlib import Path
from io import StringIO
from loguru import logger as log
from PySide6 import QtCore


class Headers:
    EMF = "EMF, mV"
    TIME_RAW = "Time, s/86400"
    TIME = "Time, s"
    TEMP = "Temperature, °C"


def parse_lines(lines: list[str]):
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

    def __init__(self, path: Path, temp_enabled: bool) -> None:
        super().__init__()
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
