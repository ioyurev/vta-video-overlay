import configparser

from loguru import logger as log
from PySide6 import QtCore

DEFAULT_CONFIG = {"Overlay": {"additional_text": "", "additional_text_enabled": False}}


class Config:
    def read_config(self, path):
        self.path = path
        self.config = configparser.ConfigParser()
        if not self.config.read(path, encoding="utf-8"):
            log.warning(
                QtCore.QCoreApplication.tr(
                    "Config file not found or corrupted. Creating new config file."
                )
            )
            self.config.read_dict(DEFAULT_CONFIG)
            self.write_config()

        self.additional_text_enabled = self.config["Overlay"].getboolean(
            "additional_text_enabled"
        )
        self.additional_text = self.config["Overlay"]["additional_text"]
        log.info(QtCore.QCoreApplication.tr("Config loaded."))
        log.info(f"additional_text_enabled: {self.additional_text_enabled}")
        log.info(f"additional_text: {self.additional_text}")

    def write_config(self):
        with open(self.path, "w") as configfile:
            self.config.write(configfile)


config = Config()
