from pathlib import Path

import cv2
from loguru import logger as log
from PySide6 import QtCore

from .crop_selection_widgets import RectangleGeometry
from .data_collections import ProcessProgress
from .opencv_frame import Alignment, Frame, cv_get_text_size
from .plotter import Plotter
from .video_data import VideoData

CODEC = "mp4v"
TEXT_COLOR = (0, 255, 255)
BG_COLOR = (63, 63, 63)


class CVProcessor(QtCore.QObject):
    def __init__(
        self,
        video_data: VideoData,
        path_output: Path,
        progress_signal: QtCore.Signal,
        plot_enabled: bool,
        crop_rect: RectangleGeometry | None = None,
        parent=None,
    ):
        super().__init__(parent=parent)
        self.video_data = video_data
        self.path_output = path_output
        self.path_input = video_data.path
        self.temp_enabled = video_data.temp_enabled
        self.progress_signal = progress_signal
        self.plot_enabled = plot_enabled
        self.crop_rect = crop_rect
        self.video_data.prepare()
        if self.plot_enabled:
            self.plotter = Plotter(video_data=self.video_data)
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

    def loop(self, current_progress: int, start_timestamp: float):
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
                frame.crop(
                    x=self.crop_rect.x,
                    y=self.crop_rect.y,
                    w=self.crop_rect.w,
                    h=self.crop_rect.h,
                )
            if self.temp_enabled:
                value = self.video_data.temp_aligned[frame_index]
            else:
                value = self.video_data.emf_aligned[frame_index]
            frame.put_text(
                text=self.tmp_str_temp.format(temp=value),
                x=5,
                y=5,
                align=Alignment.TOP_LEFT,
                color=TEXT_COLOR,
                bg_color=BG_COLOR,
                margin=5,
                scale=2.0,
            )
            frame.put_text(
                text=self.str_sample,
                x=5,
                y=frame.size.height - 5,
                align=Alignment.BOTTOM_LEFT,
                color=TEXT_COLOR,
                bg_color=BG_COLOR,
                margin=5,
                scale=2.0,
            )
            frame.make_border(bottom=self.text_height)
            frame.put_text(
                text=self.str_operator,
                x=5,
                y=frame.size.height - 5,
                align=Alignment.BOTTOM_LEFT,
                color=TEXT_COLOR,
                bg_color=BG_COLOR,
                margin=5,
            )
            if self.plot_enabled:
                self.plotter.draw(index=frame_index)
                plot_img = self.plotter.get_image()
                plot_img = cv2.cvtColor(plot_img, cv2.COLOR_RGB2BGR)
                # paste img at right top corner
                x = frame.shape[1] - plot_img.shape[1]
                y = 0
                cv_paste_image(img1=frame, img2=plot_img[:, :, :3], x=x, y=y)
            self.video_output.write(frame.image)
            progress = current_progress + int((100 * frame_index / self.maxindex) // 3)
            self.progress_signal.emit(ProcessProgress(value=progress, frame=frame))
        return progress

    def run(self, current_progress: int, start_timestamp: float):
        self.video_input = cv2.VideoCapture(str(self.path_input))
        frame_width = int(self.video_input.get(3))
        frame_height = int(self.video_input.get(4))
        self.text_height = cv_get_text_size("").height * 2
        if self.crop_rect is not None:
            size = (self.crop_rect.w, self.crop_rect.h + self.text_height)
        else:
            size = (frame_width, frame_height + self.text_height)
        fps = self.video_input.get(cv2.CAP_PROP_FPS)
        log.info(self.tr("Video resolution: {size}").format(size=size))
        log.info(f"FPS: {fps}")
        self.video_output = cv2.VideoWriter(
            filename=str(self.path_output),
            fourcc=cv2.VideoWriter_fourcc(*CODEC),
            fps=fps,
            frameSize=size,
        )
        progress = self.loop(
            current_progress=current_progress, start_timestamp=start_timestamp
        )
        self.video_input.release()
        self.video_output.release()
        log.info(self.tr("OpenCV has finished"))
        return progress


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
