import pandas as pd
import numpy as np
from pathlib import Path
from io import StringIO


class Headers:
    EMF = "EMF, mV"
    TIME_RAW = "Time, s/86400"
    TIME = "Time, s"
    TEMP = "Temperature, Celsius degree"


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


class Data:
    operator: str
    sample: str
    coeff: list[str]

    def __init__(self, path: Path, temp_enabled: bool) -> None:
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
