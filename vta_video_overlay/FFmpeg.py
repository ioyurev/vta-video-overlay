from ffmpeg_progress_yield import FfmpegProgress
from decimal import Decimal
from PySide6 import QtCore
from pathlib import Path
from typing import List
import subprocess
import json


def get_pts(packets) -> List[int]:
    pts: List[int] = []

    for packet in packets:
        pts.append(int(Decimal(packet["pts_time"]) * 1000))

    pts.sort()
    return pts


def get_timestamps(video_path: Path, index: int = 0) -> List[int]:
    # source: https://stackoverflow.com/a/73998721/11709825
    """
    Link: https://ffmpeg.org/ffprobe.html
    My comments:
        Works really well, but the user need to have FFMpeg in his environment variables.

    Parameters:
        video (pathlib.Path): Video path
        index (int): Index of the stream of the video
    Returns:
        List of timestamps in ms
        :param index:
        :param video_path:
    """

    # Getting video absolute path and checking for its existance
    video_path = video_path.resolve()
    if not video_path.is_file():
        raise FileNotFoundError(f'Invalid path for the video file: "{video_path}"')

    cmd = f'ffprobe -select_streams {index} -show_entries packet=pts_time:stream=codec_type "{video_path}" -print_format json'
    ffprobe_output = subprocess.run(cmd, capture_output=True, text=True)
    ffprobe_output = json.loads(ffprobe_output.stdout)

    if len(ffprobe_output) == 0:  # type: ignore
        raise Exception(
            f"The file {video_path} is not a video file or the file does not exist."
        )

    if len(ffprobe_output["streams"]) == 0:  # type: ignore
        raise ValueError(f"The index {index} is not in the file {video_path}.")

    if ffprobe_output["streams"][0]["codec_type"] != "video":  # type: ignore
        raise ValueError(
            f'The index {index} is not a video stream. It is an {ffprobe_output["streams"][0]["codec_type"]} stream.'  # type: ignore
        )

    return get_pts(ffprobe_output["packets"])  # type: ignore


def convert_video(
    path_input: Path, path_output: Path, signal: QtCore.Signal, current_progress: int
):
    cmd = ["ffmpeg", "-i", str(path_input), str(path_output)]
    ff = FfmpegProgress(cmd)
    print(f"* Конвертирование файла: {path_input}")
    print(f"* Сохранение по пути: {path_output}")
    for ff_progress in ff.run_command_with_progress():
        val = int(round(ff_progress))
        progress = current_progress + val // 3
        signal.emit(progress)
        print(f"* Прогресс ffmpeg: {val}/100")
    print("* Работа ffmpeg завершена")
    return progress
