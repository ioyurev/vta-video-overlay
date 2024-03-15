from vta_video_overlay.TdaFile import Data
from vta_video_overlay.Worker import Worker
from vta_video_overlay.__version__ import __version__
from vta_video_overlay.AboutWindow import AboutWindow
from vta_video_overlay.DataCollections import progress_tpl
from vta_video_overlay.FFmpeg import get_resolution
from ui.MainWindow import Ui_MainWindow
from loguru import logger as log
from PySide6 import QtWidgets, QtGui
from pathlib import Path
import cv2


def cv_to_pixmap(cv_image: cv2.typing.MatLike) -> QtGui.QPixmap:
    height, width, _ = cv_image.shape
    q_image = QtGui.QImage(
        cv_image.data, width, height, QtGui.QImage.Format.Format_BGR888
    )
    pixmap = QtGui.QPixmap.fromImage(q_image)
    return pixmap


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
        self.cb_trim.clicked.connect(self.switch_sb_trim)
        self.statusbar.addWidget(QtWidgets.QLabel(__version__))

        self.about_window = AboutWindow(parent=self)
        self.actionAbout = QtGui.QAction("О программе", self)
        self.actionAbout.triggered.connect(self.show_about)
        self.menubar.addAction(self.actionAbout)
        self.video_preview.setScaledContents(True)

    def show_about(self):
        self.about_window.show()
        self.about_window.raise_()

    def switch_sb_trim(self):
        self.sb_trim.setEnabled(self.cb_trim.isChecked())

    def pick_tda(self):
        path = pick_path_open(filter="Файл VPTAnalizer(*.tda)")
        self.edit_tda.setText(path)
        self.data = Data(path=Path(path), temp_enabled=self.cb_temp.isChecked())
        self.data_to_gui()

    def pick_video(self):
        path = pick_path_open(filter="Видео(*.asf *.mp4);;Все файлы(*.*)")
        self.edit_video.setText(path)
        size = get_resolution(path)
        self.video_preview.setMinimumHeight(self.video_preview.height())
        self.video_preview.setMinimumWidth(
            int(size[0] * self.video_preview.height() / size[1])
        )

    def set_stuff_enabled(self, val: bool):
        self.btn_tda.setEnabled(val)
        self.btn_video.setEnabled(val)
        self.btn_convert.setEnabled(val)
        self.edit_tda.setEnabled(val)
        self.edit_video.setEnabled(val)
        self.edit_operator.setEnabled(val)
        self.edit_sample.setEnabled(val)
        self.edit_a0.setEnabled(val)
        self.edit_a1.setEnabled(val)
        self.edit_a2.setEnabled(val)
        self.edit_a3.setEnabled(val)
        self.cb_temp.setEnabled(val)
        self.cb_trim.setEnabled(val)
        self.cb_excel.setEnabled(val)
        self.sb_trim.setEnabled(val)

    def data_to_gui(self):
        self.edit_operator.setText(self.data.operator)
        self.edit_sample.setText(self.data.sample)
        self.edit_a0.setText(str(self.data.coeff[3]))
        self.edit_a1.setText(str(self.data.coeff[2]))
        self.edit_a2.setText(str(self.data.coeff[1]))
        self.edit_a3.setText(str(self.data.coeff[0]))
        self.sb_trim.setMaximum(self.data.data_time[-1] / 2)

    def gui_to_data(self):
        self.data.operator = self.edit_operator.text()
        self.data.sample = self.edit_sample.text()
        coeff = []
        coeff.append(self.edit_a3.text())
        coeff.append(self.edit_a2.text())
        coeff.append(self.edit_a1.text())
        coeff.append(self.edit_a0.text())
        self.data.temp_enabled = self.cb_temp.isChecked()
        self.data.coeff = coeff
        self.data.recalc_temp()

    def finished(self):
        self.raise_()
        QtWidgets.QMessageBox.information(self, "vta-video-overlay", "Работа завершена")
        self.set_stuff_enabled(True)
        self.progressbar.setValue(0)

    def update_progressbar(self, tpl: progress_tpl):
        self.update_image(frame=tpl.frame)
        self.progressbar.setValue(tpl.progress)

    def update_image(self, frame: cv2.typing.MatLike | None):
        if frame is None:
            return
        self.video_preview.setPixmap(cv_to_pixmap(frame))

    def overlay(self):
        savepath = Path(pick_path_save())
        self.gui_to_data()
        if self.cb_trim.isChecked():
            start_timestamp = self.sb_trim.value()
        else:
            start_timestamp = 0.0
        log.info(f"Оператор: {self.data.operator}")
        log.info(f"Образец: {self.data.sample}")
        log.info(f"Включен расчет температуры: {self.data.temp_enabled}")
        log.info(f"Коэффициенты: {self.data.coeff}")
        log.info(f"Начало отсечки: {start_timestamp}")
        w = Worker(
            parent=self,
            video_file_path_input=Path(self.edit_video.text()),
            video_file_path_output=savepath,
            data=self.data,
            start_timestamp=start_timestamp,
        )
        w.progress.connect(self.update_progressbar)
        w.finished.connect(self.finished)
        if self.cb_excel.isChecked():
            excelpath = Path(self.edit_tda.text()).with_suffix(".xlsx")
            self.data.to_excel(excelpath)
        self.set_stuff_enabled(False)
        w.start()
