import matplotlib.pyplot as plt
from vta_video_overlay.video_data import VideoData
import numpy as np

plt.style.use("dark_background")
FOREGROUND_COLOR = "#ffff00"
FOREGROUND_COLOR_INVERTED = "#00ffff"
plt.rcParams["axes.edgecolor"] = FOREGROUND_COLOR
plt.rcParams["axes.labelcolor"] = FOREGROUND_COLOR
plt.rcParams["xtick.color"] = FOREGROUND_COLOR
plt.rcParams["ytick.color"] = FOREGROUND_COLOR
plt.rcParams["grid.color"] = FOREGROUND_COLOR


class Plotter:
    def __init__(self, video_data: VideoData):
        self.xdata = video_data.timestamps
        self.ydata = video_data.dE_per_dt
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(111)
        self.line = self.ax.plot([], [], color=FOREGROUND_COLOR)[0]
        self.point = self.ax.scatter([], [], color="#ff0000")
        self.ax.set_xlabel("Время, с")
        self.ax.set_ylabel("dE/dt, мВ/с")
        self.fig.tight_layout()

    def draw(self, index: int):
        xdata = self.xdata[:index]
        ydata = self.ydata[:index]
        self.line.set_data(xdata, ydata)
        self.point.set_offsets(np.array([xdata[-1], ydata[-1]]))
        self.ax.set_xlim(left=xdata[-1] - 4, right=xdata[-1] + 1)
        i2 = len(xdata) - 1
        i1 = np.searchsorted(xdata, xdata[-1] - 5)
        self.ax.set_ylim(min(ydata[i1:i2]) - 0.1, max(ydata[i1:i2]) + 0.1)
        self.fig.canvas.draw()

    def get_image(self):
        img = np.array(self.fig.canvas.renderer.buffer_rgba())
        return img
