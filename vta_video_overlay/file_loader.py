"""
Module for loading files with their corresponding widgets
"""

import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from loguru import logger as log

from vta_video_overlay.data_file import Data
from vta_video_overlay.file_widget_base import FileDataWidgetBase
from vta_video_overlay.info_models import LoadedMeasurement
from vta_video_overlay.tda_file import TDAFile
from vta_video_overlay.vtaz0_file import VTAZ0File
from vta_video_overlay.vtaz1_file import VTAZ1File


def load_measurement(path: Path) -> LoadedMeasurement:
    """
    Load measurement file (.tda, .vtaz) and return Data + MeasurementInfo bundle
    """
    suffix = path.suffix.lower()

    if suffix == ".tda":
        log.debug("Loading TDA file")
        tda_file = TDAFile.load(path=path)
        return LoadedMeasurement(
            data=tda_file.to_data(),
            info=tda_file.to_info(),
        )

    elif suffix == ".vtaz":
        with ZipFile(path, "r", ZIP_DEFLATED) as zipf:
            metadata_str = zipf.read("metadata.json").decode("utf-8")
            metadata = json.loads(metadata_str)
            vtaz_version = metadata.get("vtaz_version", "0.0")

        version = float(
            vtaz_version.split(".")[0] + "." + vtaz_version.split(".")[1]
            if len(vtaz_version.split(".")) >= 2
            else vtaz_version
        )

        if version >= 1.0:
            vtaz_file = VTAZ1File.load(path=path)
        else:
            vtaz_file = VTAZ0File.load(path=path)

        return LoadedMeasurement(
            data=vtaz_file.to_data(),
            info=vtaz_file.to_info(),
        )

    else:
        raise ValueError(f"Unsupported file format: {suffix}")


def load_file_with_widget(path: Path) -> tuple[Data, FileDataWidgetBase]:
    """
    Legacy helper to load file and return both Data object and corresponding widget
    """
    suffix = path.suffix.lower()

    if suffix == ".tda":
        tda_file = TDAFile.load(path=path)
        return tda_file.to_data(), tda_file.create_widget()
    elif suffix == ".vtaz":
        with ZipFile(path, "r", ZIP_DEFLATED) as zipf:
            metadata_str = zipf.read("metadata.json").decode("utf-8")
            metadata = json.loads(metadata_str)
            vtaz_version = metadata.get("vtaz_version", "0.0")

        version = float(
            vtaz_version.split(".")[0] + "." + vtaz_version.split(".")[1]
            if len(vtaz_version.split(".")) >= 2
            else vtaz_version
        )

        if version >= 1.0:
            v_file = VTAZ1File.load(path=path)
        else:
            v_file = VTAZ0File.load(path=path)

        return v_file.to_data(), v_file.create_widget()
    else:
        raise ValueError(f"Unsupported file format: {suffix}")
