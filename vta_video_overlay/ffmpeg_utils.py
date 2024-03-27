from .data_collections import ProcessProgress
from ffmpeg_progress_yield import FfmpegProgress
from decimal import Decimal
from PySide6 import QtCore
from pathlib import Path
from typing import List
import subprocess
import json
from loguru import logger as log
import ffmpeg


def get_pts(packets) -> List[int]:
    pts: List[int] = []

    for packet in packets:
        pts.append(int(Decimal(packet["pts_time"]) * 1000))

    pts.sort()
    return pts


class FFmpeg(QtCore.QObject):
    def get_resolution(self, video_path: Path | str) -> tuple[int, int]:
        probe = ffmpeg.probe(video_path)
        video_stream = next(
            (stream for stream in probe["streams"] if stream["codec_type"] == "video"),
            None,
        )
        if video_stream is not None:
            width = video_stream["width"]
            height = video_stream["height"]
            return (width, height)
        else:
            raise Exception(self.tr("Video stream not found."))

    def get_timestamps(self, video_path: Path, index: int = 0) -> List[int]:
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
            raise FileNotFoundError(
                self.tr('Invalid path for the video file: "{path}"').format(
                    path=video_path
                )
            )

        cmd = f'ffprobe -select_streams {index} -show_entries packet=pts_time:stream=codec_type "{video_path}" -print_format json'
        ffprobe_output = subprocess.run(cmd, capture_output=True, text=True)
        ffprobe_output = json.loads(ffprobe_output.stdout)

        if len(ffprobe_output) == 0:  # type: ignore
            raise Exception(
                self.tr(
                    "The file {path} is not a video file or the file does not exist."
                ).format(path=video_path)
            )

        if len(ffprobe_output["streams"]) == 0:  # type: ignore
            raise ValueError(
                self.tr("The index {i} is not in the file {path}.").format(
                    i=index, path=video_path
                )
            )

        stream_type = ffprobe_output["streams"][0]["codec_type"]  # type: ignore
        if stream_type != "video":
            raise ValueError(
                self.tr(
                    "The index {i} is not a video stream. It is an {type} stream."
                ).format(i=index, type=stream_type)
            )

        return get_pts(ffprobe_output["packets"])  # type: ignore

    def convert_video(
        self,
        path_input: Path,
        path_output: Path,
        signal: QtCore.Signal,
        current_progress: int,
    ):
        cmd = ["ffmpeg", "-i", str(path_input), str(path_output)]
        ff = FfmpegProgress(cmd)
        log.info(self.tr("Converting file: {path}").format(path=path_input))
        log.info(self.tr("Saving to: {path}").format(path=path_output))
        for ff_progress in ff.run_command_with_progress():
            val = int(round(ff_progress))
            progress = current_progress + val // 3
            signal.emit(ProcessProgress(value=progress))
        log.info(self.tr("ffmpeg conversion finished."))
        return progress
