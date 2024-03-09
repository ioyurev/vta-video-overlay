from vta_video_overlay.TdaFile import Data
from vta_video_overlay.VIdeoData import VideoData
import cv2
import tempfile
from pathlib import Path
from ffmpeg_progress_yield import FfmpegProgress
from PySide6 import QtWidgets

FFMPEG_BIN_PATH = "ffmpeg"


class CVProcessor:
    def __init__(
        self,
        video_data: VideoData,
        path_output: Path,
        progress_bar: QtWidgets.QProgressBar,
    ):
        self.video_data = video_data
        self.path_output = path_output
        self.path_input = video_data.path
        self.temp_enabled = video_data.temp_enabled
        self.progress_bar = progress_bar
        self.maxindex = len(self.video_data.timestamps) - 1
        # self.progress_bar.setFormat(f'%p/{cv.maxindex}')
        self.progress_bar.setMaximum(self.maxindex)
        self.progress_bar.setValue(0)

    def loop(self):
        ret = True
        while ret:
            ret, frame = self.video_input.read()
            frame_index = int(self.video_input.get(cv2.CAP_PROP_POS_FRAMES)) - 1
            print(f"* OpenCV обрабатыавет кадр {frame_index}/{self.maxindex}")
            lines = [
                f"Оператор: {self.video_data.operator}",
                f"Образец: {self.video_data.sample}",
                f"Время (с): {round(self.video_data.timestamps[frame_index], 3)}",
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
            self.progress_bar.setValue(frame_index)
            ### window
            cv2.namedWindow("video", cv2.WINDOW_NORMAL)
            try:
                cv2.imshow("video", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    print("* manual break cycle")
                    break
            except Exception as err:
                print("* got exception, breaking cycle")
                print(f"\n{str(err)}")
                break
        cv2.destroyAllWindows()

    def run(self):
        self.video_input = cv2.VideoCapture(str(self.path_input))
        frame_width = int(self.video_input.get(3))
        frame_height = int(self.video_input.get(4))
        size = (frame_width, frame_height)
        fps = self.video_input.get(cv2.CAP_PROP_FPS)
        print(f"* Разрешение видео: {size}")
        print(f"* FPS: {fps}")
        self.video_output = cv2.VideoWriter(
            filename=str(self.path_output),
            fourcc=cv2.VideoWriter_fourcc(*"avc1"),
            fps=fps,
            frameSize=size,
        )
        # cv_loop(video_input=video_input, video_output=video_output, video_data=self.video_data)
        self.loop()
        # print('* opencv overlay drawing done')
        # print('* releasing video')
        self.video_input.release()
        self.video_output.release()
        print("* Работа OpenCV завершена")
        # cv2.destroyAllWindows()


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
        color=(63, 63, 63),
        thickness=-1,
    )
    cv2.putText(
        img=img,
        text=text,
        org=pos,
        fontFace=cv2.FONT_HERSHEY_COMPLEX,
        fontScale=1,
        color=(0, 255, 255),
        thickness=2,
        lineType=cv2.LINE_4,
    )


def convert_video(
    path_input: Path, path_output: Path, progress_bar: QtWidgets.QProgressBar
):
    # progress_bar.setFormat(f'%p/100')
    progress_bar.setMaximum(100)
    cmd = [FFMPEG_BIN_PATH, "-i", str(path_input), str(path_output)]
    ff = FfmpegProgress(cmd)
    print(f"* Конвертирование файла: {path_input}")
    print(f"* Сохранение по пути: {path_output}")
    for progress in ff.run_command_with_progress():
        val = int(round(progress))
        progress_bar.setValue(val)
        print(f"* Прогресс ffmpeg: {val}/100")
    print("* Работа ffmpeg завершена")


def overlay(
    video_file_path_input: Path,
    video_file_path_output: Path,
    progress_bar1: QtWidgets.QProgressBar,
    progress_bar2: QtWidgets.QProgressBar,
    data: Data,
):
    with tempfile.TemporaryDirectory() as tempdir:
        tmpfile1 = Path(tempdir + "/out1.mp4")
        tmpfile2 = Path(tempdir + "/out2.mp4")
        convert_video(
            path_input=video_file_path_input,
            path_output=Path(tmpfile1),
            progress_bar=progress_bar1,
        )
        progress_bar2.setValue(1)
        video_data = VideoData(video_path=tmpfile1, data=data)
        cv = CVProcessor(
            video_data=video_data, path_output=tmpfile2, progress_bar=progress_bar1
        )
        cv.run()
        progress_bar2.setValue(2)
        convert_video(
            path_input=tmpfile2,
            path_output=video_file_path_output,
            progress_bar=progress_bar1,
        )
        progress_bar2.setValue(3)
        QtWidgets.QMessageBox.information(None, "Отчет", "Готово!")
        # timestamps, emf_data, temp_data = fit_data(video_path=tmpfile1, data=data)


# if __name__ == '__main__':
#     tda = 'example/2024.03.06-2 Tm2S3-MnS 60-40.Tda'
#     video = 'example/converted.mp4'
#     fit_data(video_path=Path(video), data=Data(path=Path(tda)))
