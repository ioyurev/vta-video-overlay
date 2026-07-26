import numpy as np


def compute_real_fps(timestamps_sec: np.ndarray) -> float | None:
    if len(timestamps_sec) < 2:
        return None
    duration = float(timestamps_sec[-1] - timestamps_sec[0])
    if duration <= 0:
        return None
    return (len(timestamps_sec) - 1) / duration


def build_vfr_setpts_script_content(timestamps_sec: np.ndarray) -> str:
    """Генерирует скрипт фильтра setpts для FFmpeg для сохранения точных VFR меток времени (PTS)."""
    n_frames = len(timestamps_sec)
    if n_frames <= 1:
        return "setpts=N/TB"

    step = max(1, n_frames // 2500)
    seg_list = list(range(0, n_frames, step))
    if seg_list[-1] != n_frames - 1:
        seg_list.append(n_frames - 1)
    seg_indices = np.array(seg_list, dtype=int)

    parts = []
    for i in range(len(seg_indices) - 1):
        n0, n1 = seg_indices[i], seg_indices[i + 1]
        t0_val, t1_val = float(timestamps_sec[n0]), float(timestamps_sec[n1])
        slope = (t1_val - t0_val) / (n1 - n0)
        parts.append(f"gte(N\\,{n0})*lt(N\\,{n1})*({t0_val:.4f}+(N-{n0})*{slope:.6f})")
    parts.append(f"gte(N\\,{n_frames - 1})*{float(timestamps_sec[-1]):.4f}")

    setpts_expr = "+".join(parts)
    return f"setpts=({setpts_expr})/TB"

