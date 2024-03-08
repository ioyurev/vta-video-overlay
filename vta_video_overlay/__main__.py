from PySide6 import QtWidgets
from vta_video_overlay.MainWindow import MainWindow


def main():
    app = QtWidgets.QApplication()
    w = MainWindow()
    w.show()
    app.exec()


if __name__ == "__main__":
    main()
