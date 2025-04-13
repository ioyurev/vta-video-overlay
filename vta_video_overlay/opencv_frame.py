"""
OpenCV frame processing and composition utilities

Key Responsibilities:
- Core image manipulation for video overlay rendering
- Coordinate system management for text/graphic placement
- Conversion between OpenCV, PIL and Qt image formats
- Transparency-aware image compositing
- Border management and aspect ratio preservation

Implementation Details:
- Uses OpenCV's BGR color space internally
- Automatic alpha channel detection in overlays
- Text bounding box calculations with safe margins
- Numpy-based matrix operations for performance
- Qt image integration via memory buffer sharing
"""

from typing import NamedTuple

import cv2
import numpy as np
from PySide6 import QtGui

from vta_video_overlay.config import BG_COLOR, TEXT_COLOR
from vta_video_overlay.crop_selection_widgets import RectangleGeometry
from vta_video_overlay.enums import Alignment
from vta_video_overlay.pil_frame import Image, PILFrame


class Font:
    face = cv2.FONT_HERSHEY_COMPLEX
    scale = 1.0
    thickness = 2
    linetype = cv2.LINE_AA


class Size(NamedTuple):
    width: int
    height: int


class CVFrame:
    def __init__(self, image: cv2.typing.MatLike):
        self.image = image
        self._update_size()

    @staticmethod
    def from_pilframe(frame: PILFrame):
        return CVFrame(
            image=cv2.cvtColor(src=np.array(frame.image), code=cv2.COLOR_RGB2BGR)
        )

    def to_pilframe(self):
        return PILFrame(image=Image.fromarray(self.image[:, :, ::-1]))

    def _update_size(self):
        self.size = Size(self.image.shape[1], self.image.shape[0])

    def to_pixmap(self):
        bytes_per_line = 3 * self.size.width
        q_image = QtGui.QImage(
            np.ascontiguousarray(self.image.data),
            self.size.width,
            self.size.height,
            bytes_per_line,
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
        color: tuple[int, int, int] = TEXT_COLOR,
        bg_color: tuple[int, int, int] = BG_COLOR,
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

    def put_img(
        self,
        overlay_img: cv2.typing.MatLike,
        x: int,
        y: int,
        align: Alignment = Alignment.TOP_LEFT,
    ):
        """
        Накладывает изображение с учетом выравнивания и прозрачности
        :param overlay_img: Накладываемое изображение (BGR/BGRA)
        :param x: Базовая X-координата
        :param y: Базовая Y-координата
        :param align: Тип выравнивания относительно (x,y)
        :return: Модифицированное фоновое изображение
        """
        bg_h, bg_w = self.image.shape[:2]
        img_h, img_w = overlay_img.shape[:2]

        # Корректировка координат по выравниванию
        if align == Alignment.TOP_RIGHT:
            x -= img_w
        elif align == Alignment.BOTTOM_LEFT:
            y -= img_h
        elif align == Alignment.BOTTOM_RIGHT:
            x -= img_w
            y -= img_h

        # Расчет видимой области
        x1, y1 = max(x, 0), max(y, 0)
        x2, y2 = min(x + img_w, bg_w), min(y + img_h, bg_h)

        if x1 >= x2 or y1 >= y2:
            return self.image

        # Обрезка изображения для вставки
        img_x1 = x1 - x
        img_y1 = y1 - y
        img_x2 = img_x1 + (x2 - x1)
        img_y2 = img_y1 + (y2 - y1)

        cropped = overlay_img[img_y1:img_y2, img_x1:img_x2]
        roi = self.image[y1:y2, x1:x2]

        # Обработка прозрачности
        if cropped.shape[2] == 4:
            alpha = cropped[:, :, 3:4] / 255.0
            color = cropped[:, :, :3]
        else:
            alpha = np.ones_like(roi[:, :, 0:1])
            color = cropped

        # Смешивание и вставка
        blended = (color * alpha) + (roi * (1 - alpha))
        self.image[y1:y2, x1:x2] = blended.astype(np.uint8)

        return self.image


def cv_get_text_size(text: str, scale=Font.scale):
    return Size(
        *cv2.getTextSize(
            text=text,
            fontFace=Font.face,
            fontScale=scale,
            thickness=Font.thickness,
        )[0]
    )
