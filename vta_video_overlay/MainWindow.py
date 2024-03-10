from vta_video_overlay.TdaFile import Data
from vta_video_overlay.Worker import Worker
from vta_video_overlay.__version__ import __version__
from ui.MainWindow import Ui_MainWindow
from PySide6 import QtWidgets
from pathlib import Path


def pick_path_save():
    return QtWidgets.QFileDialog.getSaveFileName(filter="Видео(*.mp4)")[0]


def pick_path_open(filter="Все файлы(*.*)"):
    return QtWidgets.QFileDialog.getOpenFileName(filter=filter)[0]


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    data: Data

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.btn_tda.clicked.connect(self.pick_tda)
        self.btn_video.clicked.connect(self.pick_video)
        self.btn_convert.clicked.connect(self.overlay)
        self.statusbar.addWidget(QtWidgets.QLabel(__version__))

    def pick_tda(self):
        path = pick_path_open(filter="Файл VPTAnalizer(*.tda)")
        self.edit_tda.setText(path)
        self.data = Data(path=Path(path), temp_enabled=self.cb_temp.isChecked())
        self.data_to_gui()

    def pick_video(self):
        path = pick_path_open(filter="Видео(*.asf *.mp4);;Все файлы(*.*)")
        self.edit_video.setText(path)

    def data_to_gui(self):
        self.edit_operator.setText(self.data.operator)
        self.edit_sample.setText(self.data.sample)
        self.edit_a0.setText(str(self.data.coeff[3]))
        self.edit_a1.setText(str(self.data.coeff[2]))
        self.edit_a2.setText(str(self.data.coeff[1]))
        self.edit_a3.setText(str(self.data.coeff[0]))

    def gui_to_data(self):
        self.data.operator = self.edit_operator.text()
        self.data.sample = self.edit_sample.text()
        coeff = []
        coeff.append(self.edit_a3.text())
        coeff.append(self.edit_a2.text())
        coeff.append(self.edit_a1.text())
        coeff.append(self.edit_a0.text())
        self.data.coeff = coeff
        self.data.recalc_temp()

    def finished(self):
        self.raise_()
        QtWidgets.QMessageBox.information(self, "vta-video-overlay", "Работа завершена")
        self.setEnabled(True)
        self.progressbar.setValue(0)

    def update_progressbar(self, val: int):
        self.progressbar.setValue(val)

    def overlay(self):
        savepath = Path(pick_path_save())
        self.gui_to_data()
        w = Worker(
            parent=self,
            video_file_path_input=Path(self.edit_video.text()),
            video_file_path_output=savepath,
            data=self.data,
        )
        w.progress.connect(self.update_progressbar)
        w.finished.connect(self.finished)
        if self.cb_excel.isChecked():
            excelpath = Path(self.edit_tda.text()).with_suffix(".xlsx")
            self.data.to_excel(excelpath)
        self.setEnabled(False)
        w.start()
