"""
Alignment enumeration definitions

Key Responsibilities:
- Provide standardized position identifiers for UI element placement
- Centralize visual alignment options for consistent layout management
- Enable type-safe positional references across rendering components

Main Components:
- Alignment: Enumeration defining:
  - TOP_LEFT: Top-left corner positioning
  - TOP_RIGHT: Top-right corner positioning
  - BOTTOM_LEFT: Bottom-left corner positioning
  - BOTTOM_RIGHT: Bottom-right corner positioning
  - CENTER: Centered positioning

Dependencies:
- enum.Enum: Base enumeration type
- enum.auto: Automatic value assignment

Used By:
- opencv_frame: For text/image positioning in video frames
- pil_frame: For overlay element placement coordinates
"""

from enum import Enum, auto


class Alignment(Enum):
    TOP_LEFT = auto()
    TOP_RIGHT = auto()
    BOTTOM_LEFT = auto()
    BOTTOM_RIGHT = auto()
    CENTER = auto()
