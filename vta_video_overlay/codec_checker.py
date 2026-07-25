import subprocess
from functools import lru_cache
from loguru import logger as log


@lru_cache(maxsize=32)
def is_codec_working(codec_name: str) -> bool:
    """Проверяет реальную способность FFmpeg кодировать сырой видеопоток этим кодеком."""
    try:
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "rawvideo",
            "-vcodec",
            "rawvideo",
            "-s",
            "640x480",
            "-pix_fmt",
            "bgr24",
            "-r",
            "10",
            "-i",
            "-",
            "-c:v",
            codec_name,
        ]
        if codec_name in ("h264_amf", "hevc_amf"):
            cmd.extend(["-rc", "cqp", "-qp", "23"])
        elif codec_name in ("h264_nvenc", "hevc_nvenc"):
            cmd.extend(["-rc", "constqp", "-qp", "23"])
        elif codec_name in ("h264_qsv", "hevc_qsv"):
            cmd.extend(["-global_quality", "23"])
        elif codec_name in ("libx264", "libx265"):
            cmd.extend(["-crf", "23"])

        cmd.extend(["-pix_fmt", "yuv420p", "-f", "null", "-"])

        p = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        # Посылаем 5 сырых кадров BGR24 для проверки подгрузки DLL/драйверов
        raw_frame = b"\x00" * (640 * 480 * 3)
        p.communicate(input=raw_frame * 5, timeout=3)
        return p.returncode == 0
    except Exception as e:
        log.debug(f"Codec pipe test for {codec_name} failed: {e}")
        return False


@lru_cache(maxsize=1)
def get_available_codecs() -> list[tuple[str, str]]:
    """Возвращает список поддерживаемых на данном ПК кодеков в формате [(название_в_ui, имя_кодека)]."""
    all_codecs = [
        ("H.264 / AVC (libx264) - CPU", "libx264"),
        ("H.265 / HEVC (libx265) - CPU", "libx265"),
        ("NVIDIA NVENC H.264 - GPU", "h264_nvenc"),
        ("NVIDIA NVENC HEVC - GPU", "hevc_nvenc"),
        ("Intel QuickSync H.264 - GPU", "h264_qsv"),
        ("Intel QuickSync HEVC - GPU", "hevc_qsv"),
        ("AMD AMF H.264 - GPU", "h264_amf"),
        ("AMD AMF HEVC - GPU", "hevc_amf"),
        ("MPEG-4 (mpeg4)", "mpeg4"),
    ]

    working_codecs = []
    for label, codec in all_codecs:
        if is_codec_working(codec):
            working_codecs.append((label, codec))

    if not working_codecs:
        # Резервный вариант, если список пуст
        working_codecs.append(("H.264 (libx264)", "libx264"))

    return working_codecs
