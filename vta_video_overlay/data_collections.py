from typing import NamedTuple

from vta_video_overlay.opencv_frame import CVFrame


class ProcessProgress(NamedTuple):
    value: int
    frame: CVFrame | None = None


class ProcessResult(NamedTuple):
    is_success: bool
    traceback_msg: str | None = None
