import matplotlib
# Use Qt backend for interactive GUI
matplotlib.use('QtAgg')

from PySide6 import QtWidgets, QtCore
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import numpy as np

from vta_video_overlay.config import BG_COLOR_MPL, TEXT_COLOR_MPL, BG_ALPHA, setup_mpl_style, style_graph_axes


class GraphPreviewDialog(QtWidgets.QDialog):
    """Dialog window for previewing speed graph"""
    
    def __init__(self, time: np.ndarray, speed: np.ndarray, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Speed Graph Preview"))
        self.resize(900, 600)

        # Создаем фигуру и канвас
        self.figure = Figure()
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        # Layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        # Рисуем график
        self.plot(time, speed)

    def plot(self, time: np.ndarray, speed: np.ndarray):
        """Plot the speed graph with styled appearance"""
        
        # Настройка стиля и получение размеров шрифта
        title_pt, label_pt = setup_mpl_style()
        
        # Настройка шрифтов
        self.figure.patch.set_facecolor(BG_COLOR_MPL)
        self.figure.patch.set_alpha(BG_ALPHA)
        
        ax = self.figure.add_subplot(111)
        ax.set_facecolor(BG_COLOR_MPL)
        ax.patch.set_alpha(0.0)
        
        # Рисуем график
        ax.plot(time, speed, color=TEXT_COLOR_MPL, linewidth=1.5, label='dT/dt')
        
        # Стилизация осей
        style_graph_axes(ax, label_pt)
        
        # Настройка осей
        ax.set_xlabel('Time (s)', color=TEXT_COLOR_MPL, fontsize=label_pt)
        
        # Заголовок вместо ylabel (справа, компактно)
        ax.set_title(
            'Speed (°C/s)', 
            color=TEXT_COLOR_MPL, 
            fontsize=title_pt, 
            loc='right', 
            pad=3
        )
        
        # Сетка
        ax.grid(True, alpha=0.3, color=TEXT_COLOR_MPL)
        
        ax.legend(facecolor=BG_COLOR_MPL, edgecolor=TEXT_COLOR_MPL, labelcolor=TEXT_COLOR_MPL)
        
        self.canvas.draw()

    def sizeHint(self):
        return QtCore.QSize(900, 600)
