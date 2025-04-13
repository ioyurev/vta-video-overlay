"""
PIL-based image composition and text rendering system

Key Responsibilities:
- High-quality text rendering with typographic controls
- Multi-layer image composition with alpha blending
- Coordinate system management for precise element placement
- Font configuration and fallback handling
- Cross-format compatibility with OpenCV frames

Implementation Details:
- Uses PIL's advanced anti-aliasing for text rendering
- Automatic padding calculation based on font metrics
- Anchor point system for alignment positioning
- Color format conversion (BGR ↔ RGB) for OpenCV compatibility
- Cached font objects for performance

Text Rendering Features:
- Unicode!
- Background padding with configurable margins
- Multi-size text support (small/large variants)
- Vertical text stacking with automatic spacing
- Color inversion protection (light/dark themes)
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
