"""
OpenCV-based video processing pipeline

Key Responsibilities:
- Execute frame-by-frame video processing with overlay operations
- Coordinate video I/O stream management
- Implement core image processing workflow
- Emit processing progress updates

Main Components:
- CVProcessor: Main processing class handling:
  - Video stream input/output management
  - Frame processing loop execution
  - Progress signal emission
- Frame composition utilities for:
  - Text overlay rendering
  - Logo positioning and blending
  - Coordinate system transformations

Dependencies:
- OpenCV (cv2): Video capture/write operations
- numpy: Image array manipulations
- .video_data: Video metadata and aligned sensor data
- .config: Overlay configuration settings
- .data_collections: ProcessProgress signaling
- .opencv_frame: CVFrame processing utilities
- PySide6.QtCore: Signal emission for UI integration

Processing Flow:
1. Initialize video streams
2. Process frames with configured overlays
3. Handle coordinate system conversions
4. Write output video
5. Emit progress updates
"""

from pathlib import Path
from typing import Final

import cv2
from loguru import logger as log
from PySide6 import QtCore

from vta_video_overlay.config import config
from vta_video_overlay.crop_selection_widgets import RectangleGeometry
from vta_video_overlay.data_collections import ProcessProgress
from vta_video_overlay.opencv_frame import Alignment, CVFrame
from vta_video_overlay.video_data import VideoData

CODEC: Final = "mp4v"


class CVProcessor(QtCore.QObject):
    progress_signal = QtCore.Signal(ProcessProgress)

    def __init__(
        self,
        video_data: VideoData,
        path_output: Path,
        crop_rect: RectangleGeometry | None = None,
    ):
        super().__init__()
        self.video_data = video_data
        self.path_output = path_output
        self.path_input = video_data.path
        self.temp_enabled = video_data.temp_enabled
        self.crop_rect = crop_rect

    def loop(self):
        self.video_input.set(cv2.CAP_PROP_POS_MSEC, 0)
        ret = True
        frame_index = 0
        while ret:
            ret, img = self.video_input.read()
            if not ret:
                log.warning(
                    self.tr("Frame read failed | Frame: {} | Pos: {:.1f}s"),
                    frame_index,
                    self.video_input.get(cv2.CAP_PROP_POS_MSEC) / 1000,
                )
                break
            frame_index = int(self.video_input.get(cv2.CAP_PROP_POS_FRAMES)) - 1
            if frame_index < 0:
                continue

            if self.temp_enabled:
                temp = self.video_data.temp_aligned[frame_index]
            else:
                temp = None
            if config.additional_text_enabled:
                add_text = config.additional_text
            else:
                add_text = None

            frame = make_frame(
                img=img,
                crop_rect=self.crop_rect,
                time=self.video_data.timestamps[frame_index],
                emf=self.video_data.emf_aligned[frame_index],
                temp=temp,
                operator_name=self.tr("Operator: {operator}").format(
                    operator=self.video_data.operator
                ),
                sample_name=self.tr("Sample: {sample}").format(
                    sample=self.video_data.sample
                ),
                add_text=add_text,
            )
            self.video_output.write(frame.image)
            self.progress_signal.emit(ProcessProgress(value=frame_index, frame=frame))

    def run(self):
        self.video_input = cv2.VideoCapture(str(self.path_input))
        frame_width = int(self.video_input.get(3))
        frame_height = int(self.video_input.get(4))
        if self.crop_rect is not None:
            size = (self.crop_rect.w, self.crop_rect.h)
        else:
            size = (frame_width, frame_height)
        fps = self.video_input.get(cv2.CAP_PROP_FPS)
        log.info(self.tr("Video resolution: {size}").format(size=size))
        log.info(f"FPS: {fps}")
        self.video_output = cv2.VideoWriter(
            filename=str(self.path_output),
            fourcc=cv2.VideoWriter_fourcc(*CODEC),
            fps=fps,
            frameSize=size,
        )
        self.loop()
        self.video_input.release()
        self.video_output.release()
        log.info(self.tr("OpenCV has finished"))


def make_frame(
    img: cv2.typing.MatLike,
    crop_rect: RectangleGeometry | None,
    time: float,
    emf: float,
    temp: float | None,
    operator_name: str,
    sample_name: str,
    add_text: str | None,
):
    cvframe = CVFrame(image=img)
    if crop_rect is not None:
        cvframe.crop_by_rect(crop_rect)
    if config.logo_enabled:
        cvframe.put_img(
            overlay_img=config.logo_img,
            x=cvframe.image.shape[1],
            y=cvframe.image.shape[0],
            align=Alignment.BOTTOM_RIGHT,
        )
    pilframe = cvframe.to_pilframe()
    bbox = pilframe.put_text(
        text=QtCore.QCoreApplication.tr("t(s): {time:.1f}").format(time=time),
        xy=(5, 5),
        align=Alignment.TOP_LEFT,
    )
    bbox = pilframe.put_text(
        text=QtCore.QCoreApplication.tr("E(mV): {emf:.2f}").format(emf=emf),
        xy=(5, 10 + bbox[3]),
        align=Alignment.TOP_LEFT,
    )
    if temp is not None:
        pilframe.put_text(
            text=f"T(°C): {temp:.0f}",
            xy=(5, 10 + bbox[3]),
            align=Alignment.TOP_LEFT,
        )
    if config.additional_text_enabled:
        bbox = pilframe.put_text(
            text=add_text,
            xy=(5, cvframe.size.height - 5),
            align=Alignment.BOTTOM_LEFT,
            small=True,
        )
        xy = (5, bbox[1] - 10)
    else:
        xy = (5, cvframe.size.height - 5)
    bbox = pilframe.put_text(
        text=operator_name, xy=xy, align=Alignment.BOTTOM_LEFT, small=True
    )
    bbox = pilframe.put_text(
        text=sample_name,
        xy=(5, bbox[1] - 10),
        align=Alignment.BOTTOM_LEFT,
    )
    cvframe = CVFrame.from_pilframe(frame=pilframe)
    return cvframe
