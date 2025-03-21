from pathlib import Path

import cv2
from loguru import logger as log
from PySide6 import QtCore

from .config import config
from .crop_selection_widgets import RectangleGeometry
from .data_collections import ProcessProgress
from .opencv_frame import Alignment, Frame, cv_get_text_size
from .video_data import VideoData

CODEC = "mp4v"
TEXT_HEIGHT = cv_get_text_size("").height * 2
TEXT_HEIGHT_2 = cv_get_text_size(text="", scale=2.0).height * 2


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
        self.maxindex = len(self.video_data.timestamps) - 1

    def make_text_templates(self):
        self.str_operator = self.tr("Operator: {operator}").format(
            operator=self.video_data.operator
        )
        self.str_sample = self.tr("Sample: {sample}").format(
            sample=self.video_data.sample
        )
        self.tmp_str_time = self.tr("t(s): {time:.1f}")
        self.tmp_str_emf = self.tr("E(mV): {emf:.2f}")
        self.tmp_str_temp = "T(C): {temp:.0f}"

    def loop(self, start_timestamp: float):
        self.video_input.set(cv2.CAP_PROP_POS_MSEC, start_timestamp * 1000)
        first_frame_index = int(self.video_input.get(cv2.CAP_PROP_POS_FRAMES))
        log.info(
            self.tr("Time trim: {timestamp}, frame: {i}").format(
                timestamp=start_timestamp, i=first_frame_index
            )
        )
        self.make_text_templates()
        ret = True
        while ret:
            ret, frame = self.video_input.read()
            if not ret:
                break
            frame_index = int(self.video_input.get(cv2.CAP_PROP_POS_FRAMES)) - 1
            if frame_index < 0:
                continue
            timestamp = self.video_data.timestamps[frame_index]
            if timestamp < start_timestamp:
                continue

            frame = Frame(frame)
            if self.crop_rect is not None:
                frame.crop_by_rect(self.crop_rect)
            # top left
            frame.put_text(
                text=self.tmp_str_time.format(
                    time=self.video_data.timestamps[frame_index]
                ),
                x=5,
                y=5,
                align=Alignment.TOP_LEFT,
                margin=5,
                scale=2.0,
            )
            frame.put_text(
                text=self.tmp_str_emf.format(
                    emf=self.video_data.emf_aligned[frame_index]
                ),
                x=5,
                y=5 + TEXT_HEIGHT_2,
                align=Alignment.TOP_LEFT,
                margin=5,
                scale=2.0,
            )
            if self.temp_enabled:
                frame.put_text(
                    text=self.tmp_str_temp.format(
                        temp=self.video_data.temp_aligned[frame_index]
                    ),
                    x=5,
                    y=5 + TEXT_HEIGHT_2 * 2,
                    align=Alignment.TOP_LEFT,
                    margin=5,
                    scale=2.0,
                )
            # bottom left
            if config.additional_text_enabled:
                frame.put_text(
                    text=config.additional_text,
                    x=5,
                    y=frame.size.height - 5,
                    align=Alignment.BOTTOM_LEFT,
                    margin=5,
                )
                sample_name_y = frame.size.height - 5 - TEXT_HEIGHT * 2
                operator_y = frame.size.height - 5 - TEXT_HEIGHT
            else:
                sample_name_y = frame.size.height - 5 - TEXT_HEIGHT
                operator_y = frame.size.height - 5
            frame.put_text(
                text=self.str_operator,
                x=5,
                y=operator_y,
                align=Alignment.BOTTOM_LEFT,
                margin=5,
            )
            frame.put_text(
                text=self.str_sample,
                x=5,
                y=sample_name_y,
                align=Alignment.BOTTOM_LEFT,
                margin=5,
                scale=1.5,
            )
            # if self.plot_enabled:
            #     self.plotter.draw(index=frame_index)
            #     plot_img = self.plotter.get_image()
            #     plot_img = cv2.cvtColor(plot_img, cv2.COLOR_RGB2BGR)
            #     # paste img at right top corner
            #     x = frame.shape[1] - plot_img.shape[1]
            #     y = 0
            #     cv_paste_image(img1=frame, img2=plot_img[:, :, :3], x=x, y=y)
            self.video_output.write(frame.image)
            self.progress_signal.emit(ProcessProgress(value=frame_index, frame=frame))

    def run(self, start_timestamp: float):
        self.video_input = cv2.VideoCapture(str(self.path_input))
        frame_width = int(self.video_input.get(3))
        frame_height = int(self.video_input.get(4))
        # add_height = TEXT_HEIGHT * (1 + int(config.additional_text_enabled))
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
        self.loop(start_timestamp=start_timestamp)
        self.video_input.release()
        self.video_output.release()
        log.info(self.tr("OpenCV has finished"))


def cv_paste_image(
    img1: cv2.typing.MatLike, img2: cv2.typing.MatLike, x: int = 0, y: int = 0
):
    """
    Paste img2 onto img1 at the specified location.
    """
    # Get the dimensions of img2
    height, width, _ = img2.shape

    # Create a region of interest (ROI) on img1
    roi = img1[y : y + height, x : x + width]

    # Make the ROI black
    roi[:] = (0, 0, 0)

    # Add img2 to the ROI
    roi[:, :, :3] = img2
