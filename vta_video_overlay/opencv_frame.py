from typing import NamedTuple

import cv2
import numpy as np
from PySide6 import QtGui

from vta_video_overlay.crop_selection_widgets import RectangleGeometry
from vta_video_overlay.enums import Alignment
from vta_video_overlay.pil_frame import Image, PILFrame


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
            np.ascontiguousarray(self.image.data),  # type: ignore
            self.size.width,
            self.size.height,
            bytes_per_line,
            QtGui.QImage.Format.Format_BGR888,
        )  # type: ignore
        return QtGui.QPixmap.fromImage(q_image)

    def crop(self, x: int, y: int, w: int, h: int):
        self.image = self.image[y : y + h, x : x + w].copy()
        self._update_size()

    def crop_by_rect(self, rect: RectangleGeometry):
        # Validate crop parameters to prevent invalid operations
        h, w = self.image.shape[:2]
        # Ensure crop coordinates are within image bounds
        x = max(0, min(rect.x, w - 1))
        y = max(0, min(rect.y, h - 1))
        # Ensure crop dimensions are positive and don't exceed image bounds
        crop_w = max(10, min(rect.w, w - x))  # Minimum 10 pixels width
        crop_h = max(10, min(rect.h, h - y))  # Minimum 10 pixels height
        self.crop(x, y, crop_w, crop_h)

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
