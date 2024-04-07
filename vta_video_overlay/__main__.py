import locale
import os
import shutil
import sys

from loguru import logger as log
from PySide6 import QtCore, QtWidgets

import vta_video_overlay.ui.resources_rc  # noqa: F401
from vta_video_overlay.main_window import MainWindow


def setup_logging():
    app_folder = "vta_video_overlay"
    if sys.platform.startswith("linux"):
        appdata_folder = os.environ.get(
            "XDG_DATA_HOME", os.path.expanduser("~/.local/share")
        )
    else:
        appdata_folder = os.getenv("APPDATA")
    app_folder_path = os.path.join(appdata_folder, app_folder)

    if not os.path.exists(app_folder_path):
        os.makedirs(app_folder_path)

    log_file_path = os.path.join(app_folder_path, "logs/{time}.log")
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

    def run(self):
        if not self.check_environment():
            return
        self.set_language()
        w = MainWindow()
        w.show()
        self.exec()


if __name__ == "__main__":
    setup_logging()
    App().run()
