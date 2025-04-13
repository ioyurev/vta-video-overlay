"""
PIL-based image frame processing utilities

Key Responsibilities:
- Handle Pillow (PIL) image manipulation and annotation
- Implement text rendering with alignment and styling
- Manage image overlay composition and blending
- Provide conversion between PIL and other image formats

Main Components:
- PILFrame: Core image container implementing:
  - Text annotation with position/alignment control
  - Multi-line text rendering with padding
  - Overlay image blending with transparency
  - Conversion to/from OpenCV-compatible formats
- Font configuration management for text rendering
- Coordinate calculation utilities for element placement

Dependencies:
- PIL.Image: Core image manipulation
- PIL.ImageDraw: Text rendering capabilities
- PIL.ImageFont: Font configuration handling
- .enums: Alignment position definitions
- .config: Text/overlay styling configuration

Used By:
- opencv_processor: For converting PIL frames to OpenCV format
- main_window: For preview image generation in UI
- worker: For final output frame composition
"""

from PIL import Image, ImageDraw, ImageFont

from vta_video_overlay.config import BG_COLOR, TEXT_COLOR
from vta_video_overlay.enums import Alignment

try:
    PILFONT = ImageFont.truetype("times.ttf", 60)
    PILFONTSMALL = ImageFont.truetype("times.ttf", 40)
except Exception as e:
    print(f"Failed to load font: {e}")
    print("Fallback to default font")
    PILFONT = ImageFont.load_default(size=60)
    PILFONTSMALL = ImageFont.load_default(size=40)


class PILFrame:
    def __init__(self, image: Image):
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
        if small:
            font = PILFONTSMALL
        else:
            font = PILFONT
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
        padding = 5
        expanded_bbox = (
            bbox[0] - padding,  # left
            bbox[1] - padding,  # top
            bbox[2] + padding,  # right
            bbox[3] + padding,  # bottom
        )
        draw.rectangle(xy=expanded_bbox, fill=bg_color)
        draw.text(xy, text, fill=color[::-1], anchor=anchor, font=font)
        return expanded_bbox
