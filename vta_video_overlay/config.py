"""
Application configuration management for video overlay system

Core Functionality:
- Application environment initialization
- INI configuration file handling
- Logging system configuration
- Overlay parameters and UI settings management
- Graphic resources processing

Implementation Highlights:
- Cross-platform path handling (Windows/Linux)
- Automatic directory structure creation
- Graphic resources validation during loading
- Qt interface integration through localization system
"""

import configparser
import locale
import os
import sys
from pathlib import Path
from typing import Final

import cv2
from loguru import logger as log

DEFAULT_CONFIG: Final = {
    "Overlay": {
        "additional_text": " ",
        "additional_text_enabled": False,
        "logo_enabled": True,
        "main_text_size": 60,
        "additional_text_size": 40,
        "language": locale.getlocale()[0].split("_")[0],  # type: ignore
    }
}
log.debug(f"System language detected as {DEFAULT_CONFIG['Overlay']['language']}")
TEXT_COLOR: Final = (0, 255, 255)
BG_COLOR: Final = (63, 63, 63)


def set_appdata_folder() -> Path:
    app_folder = "vta_video_overlay"
    if sys.platform.startswith("linux"):
        appdata_folder = os.environ.get(
            "XDG_DATA_HOME", os.path.expanduser("~/.local/share")
        )
    else:
        appdata_folder = os.getenv("APPDATA")
        if appdata_folder is None:
            raise RuntimeError("Not found appdata folder")
    appdata_path = Path(os.path.join(appdata_folder, app_folder))
    if not os.path.exists(appdata_path):
        os.makedirs(appdata_path)
    return Path(appdata_path)


def setup_logging(appdata_path: Path):
    log_file_path = appdata_path / "logs/{time}.log"
    log.add(log_file_path)


class Config:
    def __init__(self, path: Path):
        self.path = path
        self.read_config()

    def read_config(self):
        self.config = configparser.ConfigParser()
        if not self.config.read(self.path, encoding="utf-8"):
            log.warning("Config file not found or corrupted. Creating new config file.")
            self.config.read_dict(DEFAULT_CONFIG)
            self.write_config()

        self.logo_enabled = self.config["Overlay"].getboolean("logo_enabled")
        if self.logo_enabled:
            try:
                self.logo_img = cv2.imread("logo.png")
                if self.logo_img is None:
                    self.logo_enabled = False
            except Exception as e:
                log.error(f"Failed to load logo file: {e}")
                self.logo_enabled = False
        self.additional_text_enabled = self.config["Overlay"].getboolean(
            "additional_text_enabled"
        )
        self.additional_text = self.config["Overlay"]["additional_text"]
        self.main_text_size = self.config["Overlay"].getint(
            "main_text_size", fallback=60
        )
        self.additional_text_size = self.config["Overlay"].getint(
            "additional_text_size", fallback=40
        )
        self.language = self.config["Overlay"]["language"]
        log.info("Config loaded.")
        log.debug(f"additional_text_enabled: {self.additional_text_enabled}")
        log.debug(f"additional_text: {self.additional_text}")
        log.debug(f"logo_enabled: {self.logo_enabled}")
        log.debug(f"main_text_size: {self.main_text_size}")
        log.debug(f"additional_text_size: {self.additional_text_size}")
        log.debug(f"language: {self.language}")

    def write_config(self):
        try:
            with open(self.path, "w") as configfile:
                self.config.write(configfile)
            log.info(
                "Config updated | Logo Enabled: {} | Text Enabled: {}",
                self.logo_enabled,
                self.additional_text_enabled,
            )
        except Exception as e:
            log.exception(e)


appdata_path = set_appdata_folder()
setup_logging(appdata_path=appdata_path)
config = Config(path=appdata_path / "config.ini")
