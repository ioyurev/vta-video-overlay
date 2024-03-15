from vta_video_overlay.VideoData import VideoData
from vta_video_overlay.DataCollections import progress_tpl
import cv2
from pathlib import Path
from PySide6 import QtCore
from loguru import logger as log

CODEC = "mp4v"
TEXT_COLOR = (0, 255, 255)
BG_COLOR = (63, 63, 63)
STOPKEY = ord("q")


class CVProcessor(QtCore.QObject):
    def __init__(
        self,
        video_data: VideoData,
        path_output: Path,
        progress_signal: QtCore.Signal,
        parent=None,
    ):
        super().__init__(parent=parent)
        self.video_data = video_data
        self.path_output = path_output
        self.path_input = video_data.path
        self.temp_enabled = video_data.temp_enabled
        self.progress_signal = progress_signal

    def prepare(self):
        self.video_data.prepare()
        self.maxindex = len(self.video_data.timestamps) - 1

    def make_text_template(self):
        template = (
            f"Оператор: {self.video_data.operator}\n"
            f"Образец: {self.video_data.sample}\n"
            f"Время (с): {{time:.3f}}\n"
            f"ЭДС (мВ): {{emf:.3f}}"
        )
        if self.temp_enabled:
            template += "\nТемпература (C): {temp:.0f}"
        return template

    def loop(self, current_progress: int, start_timestamp: float):
        self.video_input.set(cv2.CAP_PROP_POS_MSEC, start_timestamp * 1000)
        first_frame_index = int(self.video_input.get(cv2.CAP_PROP_POS_FRAMES))
        log.info(f"Отсечка по времени: {start_timestamp}\n, кадр: {first_frame_index}")
        text_template = self.make_text_template()
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
            print(f"* OpenCV обрабатывает кадр {frame_index}/{self.maxindex}")
            if self.temp_enabled:
                text = text_template.format(
                    time=timestamp,
                    emf=self.video_data.emf_aligned[frame_index],
                    temp=self.video_data.temp_aligned[frame_index],
                )
            else:
                text = text_template.format(
                    time=timestamp, emf=self.video_data.emf_aligned[frame_index]
                )
            cv_draw_text(img=frame, text=text, pos=(50, 50))
            self.video_output.write(frame)
            progress = current_progress + (100 * frame_index / self.maxindex) // 3
            self.progress_signal.emit(progress_tpl(progress=progress, frame=frame))
            if cv2.waitKey(1) & 0xFF == STOPKEY:
                log.info("Ручная остановка OpenCV")
                break
        return progress

    @log.catch
    def run(self, current_progress: int, start_timestamp: float):
        self.video_input = cv2.VideoCapture(str(self.path_input))
        frame_width = int(self.video_input.get(3))
        frame_height = int(self.video_input.get(4))
        size = (frame_width, frame_height)
        fps = self.video_input.get(cv2.CAP_PROP_FPS)
        log.info(f"Разрешение видео: {size}")
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
        cv2.destroyAllWindows()
        log.info("Работа OpenCV завершена")
        return progress


def cv_draw_text(img: cv2.typing.MatLike, text: str, pos: tuple[int, int]):
    lines = text.splitlines()
    x, y = pos
    for line in lines:
        text_size, _ = cv2.getTextSize(
            text=line, fontFace=cv2.FONT_HERSHEY_COMPLEX, fontScale=1, thickness=2
        )
        text_w, text_h = text_size
        cv2.rectangle(
            img=img,
            pt1=(x, int(y - text_h * 1.5)),
            pt2=(x + text_w, int(y + text_h / 2)),
            color=BG_COLOR,
            thickness=-1,
        )
        cv2.putText(
            img=img,
            text=line,
            org=(x, y),
            fontFace=cv2.FONT_HERSHEY_COMPLEX,
            fontScale=1,
            color=TEXT_COLOR,
            thickness=2,
            lineType=cv2.LINE_4,
        )
        y += 50
