from typing import NamedTuple
from cv2.typing import MatLike


class ProcessProgress(NamedTuple):
    value: int
    frame: MatLike | None = None


class ProcessResult(NamedTuple):
    is_success: bool
    exception: Exception | None = None
