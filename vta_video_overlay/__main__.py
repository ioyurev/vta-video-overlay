import locale
import shutil
import sys

from loguru import logger as log
from PySide6 import QtCore, QtWidgets

import vta_video_overlay.ui.resources_rc  # noqa: F401
from vta_video_overlay.controller import Controller
from vta_video_overlay.main_window import MainWindow


def close_splash():
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        import pyi_splash  # type: ignore

        pyi_splash.close()


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
        c = Controller()
        w = MainWindow(controller=c)
        w.show()
        self.exec()


if __name__ == "__main__":
    close_splash()
    App().run()
