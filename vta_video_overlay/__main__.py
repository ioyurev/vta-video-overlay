import shutil
import sys

from loguru import logger as log
from PySide6 import QtCore, QtWidgets

import vta_video_overlay.ui.resources_rc  # noqa: F401
from vta_video_overlay.config import config
from vta_video_overlay.controller import Controller
from vta_video_overlay.excepthook import set_excepthook
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
        if config.language == "Russian" or config.language == "ru":
            translator = QtCore.QTranslator(parent=self)
            translator.load(":/assets/translation_ru.qm")
            self.installTranslator(translator)

    def run(self):
        if not self.check_environment():
            return
        set_excepthook()
        self.set_language()
        c = Controller()
        w = MainWindow(controller=c)
        w.show()
        self.exec()


def main():
    """Main entry point for the application."""
    close_splash()
    App().run()


if __name__ == "__main__":
    main()
