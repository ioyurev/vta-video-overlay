import locale
import os
import shutil
import sys
from pathlib import Path

from loguru import logger as log
from PySide6 import QtCore, QtWidgets

import vta_video_overlay.ui.resources_rc  # noqa: F401
from vta_video_overlay.config import config
from vta_video_overlay.main_window import MainWindow


def set_appdata_folder():
    app_folder = "vta_video_overlay"
    if sys.platform.startswith("linux"):
        appdata_folder = os.environ.get(
            "XDG_DATA_HOME", os.path.expanduser("~/.local/share")
        )
    else:
        appdata_folder = os.getenv("APPDATA")
    appdata_path = Path(os.path.join(appdata_folder, app_folder))
    if not os.path.exists(appdata_path):
        os.makedirs(appdata_path)
    config.read_config(appdata_path / "config.ini")
    return Path(appdata_path)


def setup_logging(appdata_path: Path):
    log_file_path = appdata_path / "logs/{time}.log"
    log.add(log_file_path)


class App(QtWidgets.QApplication):
    def check_environment(self):
        for binary in ["ffmpeg", "ffprobe"]:
            if shutil.which(binary) is None:
                log.error(f"{binary} not found.")
                QtWidgets.QMessageBox.critical(
                    None,
                    self.tr("Error"),
                    self.tr("{bin} not found.").format(bin=binary),
                )
                return False
        log.debug("Environement check successful")
        return True

    def set_language(self):
        system_language = locale.getlocale()[0].split("_")[0]
        if system_language == "Russian" or system_language == "ru":
            log.debug("System language detected as Russian")
            translator = QtCore.QTranslator(parent=self)
            translator.load(":/assets/translation_ru.qm")
            self.installTranslator(translator)

    def run(self, appdata_path: Path):
        if not self.check_environment():
            return
        self.set_language()
        w = MainWindow(appdata_path / "logs")
        w.show()
        self.exec()


if __name__ == "__main__":
    appdata_path = set_appdata_folder()
    setup_logging(appdata_path)
    App().run(appdata_path)
