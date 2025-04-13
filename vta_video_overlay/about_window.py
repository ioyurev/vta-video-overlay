"""
About dialog window implementation

Key Responsibilities:
- Displays application metadata and credits
- Shows version information from __version__
- Provides links to repository and author contact

Main Components:
- AboutWindow: QDialog subclass containing:
  - Application logo display
  - Version information label
  - Author contact information
  - Repository link

Dependencies:
- PySide6.QtWidgets: Dialog and layout management
- PySide6.QtGui: Image handling for logo display
- PySide6.QtCore: Translation support
- .__version__: For current version display
"""

from typing import Final

from PySide6 import QtCore, QtGui, QtWidgets

from vta_video_overlay.__version__ import __version__

REPO_LINK: Final = "https://gitflic.ru/project/i-o-yurev/vta-video-overlay"
AUTHOR_EMAIL: Final = "i.o.yurev@yandex.ru"


class AboutWindow(QtWidgets.QDialog):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.setWindowTitle(self.tr("About"))
        layout = QtWidgets.QVBoxLayout()

        logo_pixmap = QtGui.QPixmap(":/assets/icon.png")
        logo_label = QtWidgets.QLabel()
        logo_label.setPixmap(
            logo_pixmap.scaledToWidth(
                200, QtGui.Qt.TransformationMode.SmoothTransformation
            )
        )
        layout.addWidget(logo_label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)

        label = QtWidgets.QLabel(self.tr("Program for overlaying VTA data on video."))
        layout.addWidget(label)

        label = QtWidgets.QLabel(
            self.tr('Ilya O. Yurev, <a href="mailto:{email}">{email}</a>').format(
                email=AUTHOR_EMAIL
            )
        )
        label.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextBrowserInteraction
        )
        label.setOpenExternalLinks(True)
        layout.addWidget(label)

        label = QtWidgets.QLabel(self.tr("Version: {v}").format(v=__version__))
        layout.addWidget(label)

        repo_link = QtWidgets.QLabel(f'<a href="{REPO_LINK}">{REPO_LINK}</a>')
        repo_link.setOpenExternalLinks(True)
        layout.addWidget(repo_link)

        self.setLayout(layout)
