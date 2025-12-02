"""
OpenCV video processing pipeline and overlay composition system

Key Responsibilities:
- Manage complete OpenCV video processing workflow from input to output
- Coordinate frame-by-frame overlay application and rendering
- Handle video stream I/O
- Maintain synchronization between video frames and sensor data
- Implement resolution-aware cropping and scaling

Processing Flow:
1. Video input initialization with resolution detection
2. Crop application (if specified) using RectangleGeometry
3. Per-frame processing:
   a) Base frame acquisition
   b) Logo overlay application (if enabled)
   c) Text/metadata rendering
   d) Temperature display (if calibrated)
4. Output stream writing
5. Progress tracking and signal emission

Performance Considerations:
- Zero-copy frame operations where possible
- Pre-calculated sensor data arrays
- Batched OpenCV operations
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

            if self.video_data.temp_aligned is not None:
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
            # Validate crop rectangle dimensions to prevent invalid video creation
            crop_w = max(10, min(self.crop_rect.w, frame_width))
            crop_h = max(10, min(self.crop_rect.h, frame_height))
            # Ensure crop coordinates don't exceed frame boundaries
            crop_x = min(self.crop_rect.x, frame_width - crop_w)
            crop_y = min(self.crop_rect.y, frame_height - crop_h)
            size = (crop_w, crop_h)
            # Update crop_rect with validated values
            self.crop_rect = RectangleGeometry(crop_x, crop_y, crop_w, crop_h)
        else:
            size = (frame_width, frame_height)
        fps = self.video_input.get(cv2.CAP_PROP_FPS)
        log.info(self.tr("Video resolution: {size}").format(size=size))
        log.info(f"FPS: {fps}")
        self.video_output = cv2.VideoWriter(
            filename=str(self.path_output),
            fourcc=cv2.VideoWriter_fourcc(*CODEC),  # type: ignore
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
        text=QtCore.QCoreApplication.tr("t(s): {time:.1f}").format(time=time),  # type: ignore
        xy=(5, 5),
        align=Alignment.TOP_LEFT,
    )
    bbox = pilframe.put_text(
        text=QtCore.QCoreApplication.tr("E(mV): {emf:.2f}").format(emf=emf),  # type: ignore
        xy=(5, 10 + bbox[3]),
        align=Alignment.TOP_LEFT,
    )
    if temp is not None:
        pilframe.put_text(
            text=f"T(°C): {temp:.0f}",
            xy=(5, 10 + bbox[3]),
            align=Alignment.TOP_LEFT,
        )
    if add_text is not None:
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
