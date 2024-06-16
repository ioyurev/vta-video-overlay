from enum import Enum
from typing import NamedTuple

import cv2
from PySide6 import QtGui
from .crop_selection_widgets import RectangleGeometry


class Alignment(Enum):
    TOP_LEFT = 0
    TOP_RIGHT = 1
    BOTTOM_LEFT = 2
    BOTTOM_RIGHT = 3
    CENTER = 4


class Font:
    face = cv2.FONT_HERSHEY_COMPLEX
    scale = 1.0
    thickness = 2
    linetype = cv2.LINE_AA


class Size(NamedTuple):
    width: int
    height: int


class Frame:
    def __init__(self, image: cv2.typing.MatLike):
        self.image = image
        self._update_size()

    def _update_size(self):
        self.size = Size(self.image.shape[1], self.image.shape[0])

    def to_pixmap(self):
        q_image = QtGui.QImage(
            self.image.data,
            self.size.width,
            self.size.height,
            QtGui.QImage.Format.Format_BGR888,
        )
        return QtGui.QPixmap.fromImage(q_image)

    def crop(self, x: int, y: int, w: int, h: int):
        self.image = self.image[y : y + h, x : x + w].copy()
        self._update_size()

    def crop_by_rect(self, rect: RectangleGeometry):
        self.crop(rect.x, rect.y, rect.w, rect.h)

    def make_border(
        self, top=0, bottom=0, left=0, right=0, color: tuple[int, int, int] = (0, 0, 0)
    ):
        self.image = cv2.copyMakeBorder(
            self.image,
            top=top,
            bottom=bottom,
            left=left,
            right=right,
            borderType=cv2.BORDER_CONSTANT,
            value=color,
        )
        self._update_size()

    def put_text(
        self,
        text: str,
        x: int,
        y: int,
        align: Alignment,
        color: tuple[int, int, int] = (255, 255, 255),
        bg_color: tuple[int, int, int] | None = None,
        margin=0,
        scale=Font.scale,
    ):
        text_size = cv_get_text_size(text, scale=scale)
        if align == Alignment.TOP_RIGHT:
            text_x = x - text_size.width - margin
            text_y = y + text_size.height + margin
        elif align == Alignment.TOP_LEFT:
            text_x = x = margin
            text_y = y + text_size.height + margin
        elif align == Alignment.BOTTOM_LEFT:
            text_x = x + margin
            text_y = y - text_size.height // 2 - margin
        elif align == Alignment.BOTTOM_RIGHT:
            text_x = x - text_size.width - margin
            text_y = y - text_size.height // 2 - margin
        elif align == Alignment.CENTER:
            text_x = x - text_size.width // 2
            text_y = y - text_size.height // 2
        if bg_color is not None:
            pt1 = (text_x - margin, text_y - text_size.height - margin)
            pt2 = (
                text_x + text_size.width + margin,
                text_y + text_size.height // 2 + margin,
            )
            cv2.rectangle(self.image, pt1, pt2, bg_color, cv2.FILLED)
        cv2.putText(
            self.image,
            text,
            (text_x, text_y),
            Font.face,
            scale,
            color,
            Font.thickness,
            cv2.LINE_AA,
        )


def cv_get_text_size(text: str, scale=Font.scale):
    return Size(
        *cv2.getTextSize(
            text=text,
            fontFace=Font.face,
            fontScale=scale,
            thickness=Font.thickness,
        )[0]
    )
