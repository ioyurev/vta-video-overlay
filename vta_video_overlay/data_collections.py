from typing import NamedTuple

from opencv_frame import Frame


class ProcessProgress(NamedTuple):
    value: int
    frame: Frame | None = None


class ProcessResult(NamedTuple):
    is_success: bool
    exception: Exception | None = None
