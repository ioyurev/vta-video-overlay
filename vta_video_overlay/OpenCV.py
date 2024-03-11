from vta_video_overlay.VideoData import VideoData
import cv2
from pathlib import Path
from PySide6 import QtCore
from loguru import logger as log

CODEC = "mp4v"
TEXT_COLOR = (0, 255, 255)
BG_COLOR = (63, 63, 63)
STOPKEY = ord("q")


class CVProcessor:
    def __init__(
        self,
        video_data: VideoData,
        path_output: Path,
        progress_signal: QtCore.Signal,
    ):
        self.video_data = video_data
        self.path_output = path_output
        self.path_input = video_data.path
        self.temp_enabled = video_data.temp_enabled
        self.progress_signal = progress_signal
        self.maxindex = len(self.video_data.timestamps) - 1

    def loop(self, current_progress: int, start_timestamp: float):
        cv2.namedWindow("video", cv2.WINDOW_GUI_NORMAL)
        ret = True
        self.video_input.set(cv2.CAP_PROP_POS_MSEC, start_timestamp * 1000)
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
            lines = [
                f"Оператор: {self.video_data.operator}",
                f"Образец: {self.video_data.sample}",
                f"Время (с): {round(timestamp, 3)}",
                f"ЭДС (мВ): {round(self.video_data.emf_aligned[frame_index], 3)}",
            ]
            if self.temp_enabled:
                lines.append(
                    f"Температура (C): {round(self.video_data.temp_aligned[frame_index])}"
                )
            x0 = 50
            y0, dy = 50, 50

            for i, line in enumerate(lines):
                y = y0 + i * dy
                cv_draw_text(frame, line, (x0, y))
            self.video_output.write(frame)
            progress = current_progress + (100 * frame_index / self.maxindex) // 3
            self.progress_signal.emit(progress)
            cv2.imshow("video", frame)
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
    x, y = pos
    text_size, _ = cv2.getTextSize(
        text=text, fontFace=cv2.FONT_HERSHEY_COMPLEX, fontScale=1, thickness=2
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
        text=text,
        org=pos,
        fontFace=cv2.FONT_HERSHEY_COMPLEX,
        fontScale=1,
        color=TEXT_COLOR,
        thickness=2,
        lineType=cv2.LINE_4,
    )
