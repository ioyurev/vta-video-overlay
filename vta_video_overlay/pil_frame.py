from typing import Union

from loguru import logger as log
from PIL import Image, ImageDraw, ImageFont

from vta_video_overlay.config import BG_COLOR, TEXT_COLOR, BG_ALPHA, FONT_FILENAME, config
from vta_video_overlay.enums import Alignment

FontType = Union[ImageFont.FreeTypeFont, ImageFont.ImageFont]

_font_cache: dict[tuple[str, int], FontType] = {}


def get_font(small: bool = False) -> FontType:
    size = config.text.additional_size if small else config.text.main_size
    key = (FONT_FILENAME, size)
    if key not in _font_cache:
        try:
            _font_cache[key] = ImageFont.truetype(FONT_FILENAME, size)
        except Exception as e:
            try:
                log.warning(f"Failed to load {FONT_FILENAME}: {e}. Trying system Arial...")
                _font_cache[key] = ImageFont.truetype("arial.ttf", size)
            except Exception as e2:
                log.error(f"Failed to load arial.ttf: {e2}")
                log.error("Fallback to default PIL font")
                _font_cache[key] = ImageFont.load_default()
    return _font_cache[key]


class PILFrame:
    def __init__(self, image: Image.Image):
        self.image = image

    def put_text(
        self,
        text: str,
        xy: tuple[int, int],
        align: Alignment,
        color: tuple[int, int, int] = TEXT_COLOR,
        bg_color: tuple[int, int, int] = BG_COLOR,
        padding: int = 5,
        small: bool = False,
    ):
        font = get_font(small=small)
        draw = ImageDraw.Draw(self.image)
        if align == Alignment.BOTTOM_LEFT:
            anchor = "lb"
        elif align == Alignment.BOTTOM_RIGHT:
            anchor = "rb"
        elif align == Alignment.TOP_LEFT:
            anchor = "lt"
        elif align == Alignment.TOP_RIGHT:
            anchor = "rt"

        bbox = draw.textbbox(xy=xy, text=text, anchor=anchor, font=font)
        bbox = (int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3]))
        pad = config.text.bg_padding
        expanded_bbox = (
            bbox[0] - pad,  # left
            bbox[1] - pad,  # top
            bbox[2] + pad,  # right
            bbox[3] + pad,  # bottom
        )
        
        # Рисование полупрозрачного фона через alpha blending
        if bg_color is not None:
            # Создаем временный слой для фона
            bg_layer = Image.new('RGBA', self.image.size, (0, 0, 0, 0))
            bg_draw = ImageDraw.Draw(bg_layer)
            # Рисуем прямоугольник с BG_COLOR и alpha=0.6 (153/255)
            bg_draw.rectangle(expanded_bbox, fill=(*bg_color, int(255 * BG_ALPHA)))
            # Смешиваем с основным изображением
            self.image = Image.alpha_composite(self.image.convert('RGBA'), bg_layer)
        
        # Рисуем текст
        draw = ImageDraw.Draw(self.image)
        draw.text(xy, text, fill=color[::-1], anchor=anchor, font=font)
        return expanded_bbox
