from ui.MainWindow import Ui_MainWindow
from PySide6 import QtWidgets
from vta_video_overlay.TdaFile import Data
from pathlib import Path
from Overlay import overlay


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

    def pick_tda(self):
        path = pick_path_open(filter="Файл VPTAnalizer(*.tda)")
        self.label_tda.setText(path)
        self.data = Data(path=Path(path), temp_enabled=self.cb_temp.isChecked())
        self.data_to_gui()

    def pick_video(self):
        path = pick_path_open(filter="Видео(*.asf *.mp4);;Все файлы(*.*)")
        self.label_video.setText(path)

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

    def overlay(self):
        savepath = Path(pick_path_save())
        # if not savepath.is_file():
        #     QtWidgets.QMessageBox.warning(self, 'Предупреждение', "Не выбран путь для сохранения")
        #     return
        self.gui_to_data()
        overlay(
            video_file_path_input=Path(self.label_video.text()),
            video_file_path_output=savepath,
            progress_bar1=self.pb_step,
            progress_bar2=self.pb_steps,
            data=self.data,
        )
