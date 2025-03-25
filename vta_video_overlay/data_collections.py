"""
Data container structures for processing metadata

Key Responsibilities:
- Define standardized data structures for processing progress/results
- Provide type-annotated containers for inter-module communication
- Enforce consistent data formats between components

Main Components:
- ProcessProgress: Named tuple tracking:
  - Current progress percentage
  - Optional preview frame data
- ProcessResult: Named tuple containing:
  - Success/failure status
  - Error traceback when applicable

Dependencies:
- typing.NamedTuple: For immutable data structures
- opencv_frame: CVFrame type reference
"""

from typing import NamedTuple

from .opencv_frame import CVFrame


class ProcessProgress(NamedTuple):
    value: int
    frame: CVFrame | None = None


class ProcessResult(NamedTuple):
    is_success: bool
    traceback_msg: str | None = None
