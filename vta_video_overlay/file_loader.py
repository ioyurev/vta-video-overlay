"""
Module for loading files with their corresponding widgets
"""

import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


from vta_video_overlay.data_file import Data
from vta_video_overlay.file_widget_base import FileDataWidgetBase
from vta_video_overlay.info_models import LoadedMeasurement
from vta_video_overlay.tda_file import TDAFile
from vta_video_overlay.vtaz0_file import VTAZ0File
from vta_video_overlay.vtaz1_file import VTAZ1File


def _load_vtaz_model(path: Path) -> VTAZ0File | VTAZ1File:
    with ZipFile(path, "r", ZIP_DEFLATED) as zipf:
        metadata = json.loads(zipf.read("metadata.json").decode("utf-8"))
    vtaz_version = metadata.get("vtaz_version", "0.0")
    parts = vtaz_version.split(".")
    major_minor = ".".join(parts[:2]) if len(parts) >= 2 else vtaz_version
    version = float(major_minor)
    return VTAZ1File.load(path=path) if version >= 1.0 else VTAZ0File.load(path=path)


def load_measurement(path: Path) -> LoadedMeasurement:
    """
    Load measurement file (.tda, .vtaz) and return Data + MeasurementInfo bundle
    """
    suffix = path.suffix.lower()

    if suffix == ".tda":
        src = TDAFile.load(path=path)
    elif suffix == ".vtaz":
        src = _load_vtaz_model(path)
    else:
        raise ValueError(f"Unsupported file format: {suffix}")

    return LoadedMeasurement(
        data=src.to_data(),
        info=src.to_info(),
    )


def load_file_with_widget(path: Path) -> tuple[Data, FileDataWidgetBase]:
    """
    Legacy helper to load file and return both Data object and corresponding widget
    """
    if path.suffix.lower() == ".tda":
        src = TDAFile.load(path=path)
    elif path.suffix.lower() == ".vtaz":
        src = _load_vtaz_model(path)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix.lower()}")

    return src.to_data(), src.create_widget()
