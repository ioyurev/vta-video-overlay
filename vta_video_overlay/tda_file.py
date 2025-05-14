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
    sample, operator, coeff, time, emf = load_tda(Path("measurement.tda"))

Data Handling:
- Automatic time conversion from days to seconds
- Locale-aware number parsing (Russian decimal format)
- Polynomial coefficient normalization
"""

from io import StringIO
from pathlib import Path
from typing import Final

import pandas as pd


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


def load_tda(path: Path):
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
    return sample, operator, coeff, time, emf
