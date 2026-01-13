from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
import numpy as np

from vta_video_overlay.config import (
    BG_COLOR_MPL, TEXT_COLOR, BG_ALPHA, 
    config, setup_mpl_style, style_graph_axes
)


class GraphOverlay:
    def __init__(
        self,
        data: np.ndarray,
        fps: float,
        width: int,
        height: int,
        time_window_sec: float = 30.0,
    ):
        self.data = np.nan_to_num(data, nan=0.0, posinf=0.0, neginf=0.0)
        self.fps = fps
        self.time_window_sec = time_window_sec
        self.window_frames = int(time_window_sec * fps)
        self.width = width
        self.height = height
        
        # Полная временная ось
        self.t_full = np.arange(len(data)) / fps
        
        # --- НАСТРОЙКА MATPLOTLIB ---
        self.dpi = 100
        title_pt, label_pt = setup_mpl_style()
        
        self.fig = Figure(
            figsize=(width / self.dpi, height / self.dpi),
            dpi=self.dpi,
            facecolor=BG_COLOR_MPL
        )
        
        self.ax = self.fig.add_subplot(111)
        
        self.fig.patch.set_alpha(BG_ALPHA)
        self.ax.set_facecolor(BG_COLOR_MPL)
        self.ax.patch.set_alpha(0.0)
        
        style_graph_axes(self.ax, label_pt)
        
        self.ax.set_xlabel(
            "t(s)", 
            color=(TEXT_COLOR[2]/255, TEXT_COLOR[1]/255, TEXT_COLOR[0]/255), 
            fontsize=label_pt, 
            labelpad=1
        )
        
        # Заголовок с единицами измерения (статичный)
        self.ax.set_title(
            "dT/dt (°C/s)", 
            color=(TEXT_COLOR[2]/255, TEXT_COLOR[1]/255, TEXT_COLOR[0]/255),
            fontsize=label_pt,
            loc='left',
            pad=3
        )
        
        # Линия графика
        self.line, = self.ax.plot(
            [], [], 
            color=(TEXT_COLOR[2]/255, TEXT_COLOR[1]/255, TEXT_COLOR[0]/255), 
            linewidth=config.graph.line_width,
            animated=True
        )
        
        # Маркер текущей точки
        self.marker, = self.ax.plot(
            [], [], 
            marker='o', 
            color=(1, 0, 0), 
            markersize=config.graph.marker_size, 
            clip_on=False, 
            zorder=10,
            animated=True
        )
        
        self.fig.subplots_adjust(left=0.18, right=0.95, top=0.90, bottom=0.12)
        
        self.canvas = FigureCanvasAgg(self.fig)
        
        # --- BLITTING SETUP ---
        self._background = None
        self._last_xlim = None
        self._last_ylim = None

    def _update_background(self):
        """Сохраняет статичный фон для blitting."""
        self.canvas.draw()
        self._background = self.canvas.copy_from_bbox(self.ax.bbox)

    def get_frame_overlay(self, current_idx: int) -> np.ndarray:
        """Рендерит график для текущего кадра."""
        current_time = current_idx / self.fps
        
        # Расчет границ X
        if current_time <= self.time_window_sec:
            x_min = 0.0
            x_max = max(current_time, 0.1)
        else:
            x_min = current_time - self.time_window_sec
            x_max = current_time
        
        # Расчет границ Y
        start_idx = max(0, current_idx - self.window_frames)
        end_idx = current_idx + 1
        visible_data = self.data[start_idx:end_idx]
        
        if len(visible_data) > 0:
            y_min, y_max = float(visible_data.min()), float(visible_data.max())
            margin = (y_max - y_min) * 0.1
            if margin == 0:
                margin = 1.0
            y_min -= margin
            y_max += margin
        else:
            y_min, y_max = -1.0, 1.0
        
        new_xlim = (x_min, x_max)
        new_ylim = (y_min, y_max)
        
        # Проверяем, изменились ли лимиты
        limits_changed = (
            self._background is None
            or self._last_xlim != new_xlim
            or self._last_ylim != new_ylim
        )
        
        if limits_changed:
            self.ax.set_xlim(new_xlim)
            self.ax.set_ylim(new_ylim)
            self._last_xlim = new_xlim
            self._last_ylim = new_ylim
            self._update_background()
        
        # Восстанавливаем фон
        self.canvas.restore_region(self._background)
        
        # Обновляем данные линии
        t_slice = self.t_full[:end_idx]
        data_slice = self.data[:end_idx]
        self.line.set_data(t_slice, data_slice)
        
        # Обновляем маркер
        if current_idx < len(self.data):
            self.marker.set_data([current_time], [self.data[current_idx]])
        
        # Рисуем только анимированные элементы
        self.ax.draw_artist(self.line)
        self.ax.draw_artist(self.marker)
        
        # Blit
        self.canvas.blit(self.ax.bbox)
        
        # Получаем буфер RGBA
        buf = np.asarray(self.canvas.buffer_rgba()).copy()
        
        # Конвертируем RGBA -> BGRA
        bgra = np.empty_like(buf)
        bgra[:, :, 0] = buf[:, :, 2]
        bgra[:, :, 1] = buf[:, :, 1]
        bgra[:, :, 2] = buf[:, :, 0]
        bgra[:, :, 3] = buf[:, :, 3]
        
        return bgra
