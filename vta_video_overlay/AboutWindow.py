from vta_video_overlay.__version__ import __version__
from PySide6 import QtWidgets, QtCore, QtGui

REPO_LINK = "https://gitflic.ru/project/i-o-yurev/vta-video-overlay"
AUTHOR_EMAIL = "i.o.yurev@yandex.ru"


class AboutWindow(QtWidgets.QDialog):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.setWindowTitle("О программе")
        layout = QtWidgets.QVBoxLayout()

        logo_pixmap = QtGui.QPixmap(":/assets/icon.png")
        logo_label = QtWidgets.QLabel()
        logo_label.setPixmap(
            logo_pixmap.scaledToWidth(
                200, QtGui.Qt.TransformationMode.SmoothTransformation
            )
        )
        layout.addWidget(logo_label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)

        label = QtWidgets.QLabel("Программа для обработки видео VTA.")
        layout.addWidget(label)

        label = QtWidgets.QLabel(
            f'Автор: Илья Олегович Юрьев, <a href="mailto:{AUTHOR_EMAIL}">{AUTHOR_EMAIL}</a>'
        )
        label.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextBrowserInteraction
        )
        label.setOpenExternalLinks(True)
        layout.addWidget(label)

        label = QtWidgets.QLabel(f"Версия: {__version__}")
        layout.addWidget(label)

        repo_link = QtWidgets.QLabel(f'<a href="{REPO_LINK}">{REPO_LINK}</a>')
        repo_link.setOpenExternalLinks(True)
        layout.addWidget(repo_link)

        self.setLayout(layout)
