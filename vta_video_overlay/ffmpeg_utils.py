import json
import subprocess
from decimal import Decimal
from pathlib import Path
from typing import List

import ffmpeg
from ffmpeg_progress_yield import FfmpegProgress
from loguru import logger as log
from PySide6 import QtCore

from .data_collections import ProcessProgress


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

        process = subprocess.Popen(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                str(index),
                "-show_entries",
                "packet=pts_time",
                "-of",
                "json",
                str(video_path),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            raise Exception(stderr.decode("utf-8"))

        probe: dict = json.loads(stdout.decode("utf-8"))

        return get_pts(probe["packets"])

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

    def check_for_packets(self, video_path: Path) -> bool:
        try:
            self.get_timestamps(video_path)
            return True
        except KeyError:
            return False
