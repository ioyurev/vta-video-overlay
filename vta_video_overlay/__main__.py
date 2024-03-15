from vta_video_overlay.MainWindow import MainWindow
import ui.resources_rc  # noqa: F401
from PySide6 import QtWidgets
from loguru import logger as log
import shutil


@log.catch
def check_environment():
    for binary in ["ffmpeg", "ffprobe"]:
        if shutil.which(binary) is None:
            raise Exception(f"{binary} не найден.")


def main():
    app = QtWidgets.QApplication()
    w = MainWindow()
    w.show()
    app.exec()


if __name__ == "__main__":
    log.add("logs/file_{time}.log")
    check_environment()
    main()
