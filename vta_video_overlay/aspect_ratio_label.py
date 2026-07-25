from PySide6 import QtCore, QtGui, QtWidgets


class AspectRatioLabel(QtWidgets.QLabel):
    """QLabel, который сохраняет соотношение сторон установленного pixmap."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._aspect_ratio: float = 16.0 / 9.0  # default
        self._original_pixmap: QtGui.QPixmap | None = None
        self.setMinimumSize(160, 90)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )

    def set_aspect_ratio(self, width: int, height: int) -> None:
        """Устанавливает целевое соотношение сторон."""
        if height > 0:
            self._aspect_ratio = width / height
        self.updateGeometry()

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        if self._aspect_ratio > 0:
            return int(width / self._aspect_ratio)
        return super().heightForWidth(width)

    def sizeHint(self) -> QtCore.QSize:
        w = self.width()
        return QtCore.QSize(w, self.heightForWidth(w))

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        self._update_scaled_pixmap()

    def setPixmap(self, pixmap: QtGui.QPixmap | QtGui.QImage) -> None:
        if isinstance(pixmap, QtGui.QImage):
            pixmap = QtGui.QPixmap.fromImage(pixmap)
        self._original_pixmap = pixmap
        self._update_scaled_pixmap()

    def _update_scaled_pixmap(self) -> None:
        if self._original_pixmap is None:
            return
        scaled = self._original_pixmap.scaled(
            self.size(),
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation,
        )
        super().setPixmap(scaled)
        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

