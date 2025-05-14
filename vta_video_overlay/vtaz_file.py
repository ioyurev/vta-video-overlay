import csv
import json
from io import TextIOWrapper
from pathlib import Path
from typing import TextIO, Tuple
from zipfile import ZIP_DEFLATED, ZipFile

from pydantic import BaseModel


class Metadata(BaseModel):
    sample: str
    operator: str


def read_csv(f: TextIO) -> Tuple[tuple[float, ...], tuple[float, ...]]:
    # Читаем всё содержимое и разделяем по нестандартному разделителю
    content = f.read()
    lines = [line.removesuffix(";") for line in content.strip().split("\n\n")]

    # Парсим CSV
    reader = csv.reader(lines)
    next(reader)  # Пропускаем заголовок

    x_list, y_list = [], []
    for row in reader:
        if len(row) >= 2:
            x_list.append(float(row[0]))
            y_list.append(float(row[1]))

    return tuple(x_list), tuple(y_list)


def load_vtaz(path: Path):
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
        else:
            coeff = ("0", "0", "0", "0")
    return metadata, time, emf, coeff
