from vta_video_overlay.MainWindow import MainWindow
import ui.resources_rc  # noqa: F401
from PySide6 import QtWidgets, QtCore
from loguru import logger as log
import shutil
import locale


class App(QtWidgets.QApplication):
    def check_environment(self):
        for binary in ["ffmpeg", "ffprobe"]:
            if shutil.which(binary) is None:
                raise Exception(self.tr("{bin} not found.").format(bin=binary))

    def set_language(self):
        system_language = locale.getlocale()[0].split("_")[0]
        if system_language == "Russian":
            log.debug("System language detected as Russian")
            translator = QtCore.QTranslator(parent=self)
            translator.load(":/assets/translation_ru.qm")
            self.installTranslator(translator)

    def run(self):
        self.set_language()
        self.check_environment()
        w = MainWindow()
        w.show()
        self.exec()


if __name__ == "__main__":
    log.add("logs/file_{time}.log")
    App().run()
