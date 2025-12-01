"""
Module for loading files with their corresponding widgets
"""

import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from loguru import logger as log

from vta_video_overlay.data_file import Data
from vta_video_overlay.file_widget_base import FileDataWidgetBase
from vta_video_overlay.tda_file import TDAFile
from vta_video_overlay.vtaz0_file import VTAZ0File
from vta_video_overlay.vtaz1_file import VTAZ1File


def load_vtaz_file(path: Path) -> tuple[Data, float]:
    """
    Load VTAZ file with automatic version detection.

    Args:
        path: Path to the .vtaz file

    Returns:
        Data: Unified data structure containing time, emf, temp measurements

    Raises:
        ValueError: If metadata version cannot be determined or file is invalid
        FileNotFoundError: If the specified file does not exist
    """
    # Read metadata to determine version
    with ZipFile(path, "r", ZIP_DEFLATED) as zipf:
        metadata_str = zipf.read("metadata.json").decode("utf-8")
        metadata = json.loads(metadata_str)
        vtaz_version = metadata.get("vtaz_version", "0.0")

    log.debug(f"Loading VTAZ file version={vtaz_version}")

    # Convert version to float for comparison (e.g., "1.0", "2.1", etc.)
    version_float = float(
        vtaz_version.split(".")[0] + "." + vtaz_version.split(".")[1]
        if len(vtaz_version.split(".")) >= 2
        else vtaz_version
    )

    if version_float >= 1.0:
        # Use VTAZ1File for version 1.0+
        return VTAZ1File.load(path).to_data(), version_float
    else:
        # Use VTAZFile for version 0.x
        return VTAZ0File.load(path).to_data(), version_float


def load_file_with_widget(path: Path) -> tuple[Data, FileDataWidgetBase]:
    """
    Load file and return both Data object and corresponding widget

    Args:
        path: Path to the file to load

    Returns:
        tuple of (Data object, FileDataWidgetBase)
    """
    suffix = path.suffix.lower()

    if suffix == ".tda":
        # Load TDA file
        log.debug("Loading TDA file")
        tda_file = TDAFile.load(path=path)
        data = tda_file.to_data()
        widget = tda_file.create_widget(path=path)
        return data, widget

    elif suffix == ".vtaz":
        # Load VTAZ file - need to determine if it's VTAZ0 or VTAZ1
        data, version = load_vtaz_file(path=path)

        if version >= 1.0:
            # This is a VTAZ1 file
            vtaz1_file = VTAZ1File.load(path=path)
            widget = vtaz1_file.create_widget()
        elif version == 0.0:
            # This is a VTAZ0 file
            vtaz0_file = VTAZ0File.load(path=path)
            widget = vtaz0_file.create_widget()
        else:
            raise ValueError(f"Unsupported VTAZ version: {version}")

        return data, widget

    else:
        raise ValueError(f"Unsupported file format: {suffix}")
