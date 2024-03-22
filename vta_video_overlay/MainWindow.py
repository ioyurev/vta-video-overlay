from .TdaFile import Data
from .Worker import Worker
from .__version__ import __version__
from .AboutWindow import AboutWindow
from .DataCollections import progress_tpl
from .FFmpeg import FFmpeg
from .ui.MainWindow import Ui_MainWindow
from loguru import logger as log
from PySide6 import QtWidgets, QtGui, QtCore
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
    return QtWidgets.QFileDialog.getSaveFileName(
        filter=QtCore.QCoreApplication.tr("Video(*.mp4)")
    )[0]


def pick_path_open(filter=QtCore.QCoreApplication.tr("All files(*.*)")):
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
        self.statusbar.addWidget(
            QtWidgets.QLabel(self.tr("Version: {v}").format(v=__version__))
        )
        self.about_window = AboutWindow(parent=self)
        self.actionAbout = QtGui.QAction(self.tr("About"), self)
        self.actionAbout.triggered.connect(self.show_about)
        self.menubar.addAction(self.actionAbout)
        self.video_preview.setScaledContents(True)

    @QtCore.Slot()
    def show_about(self):
        self.about_window.show()
        self.about_window.raise_()

    @QtCore.Slot()
    def switch_sb_trim(self):
        self.sb_trim.setEnabled(self.cb_trim.isChecked())

    @QtCore.Slot()
    def pick_tda(self):
        path = pick_path_open(filter=self.tr("VPTAnalizer file(*.tda)"))
        if path == "":
            return
        self.edit_tda.setText(path)
        self.data = Data(path=Path(path), temp_enabled=self.cb_temp.isChecked())
        self.data_to_gui()

    @QtCore.Slot()
    def pick_video(self):
        path = pick_path_open(filter=self.tr("Video(*.asf *.mp4);;All files(*.*)"))
        if path == "":
            return
        self.edit_video.setText(path)
        size = FFmpeg().get_resolution(video_path=path)
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
        self.cb_plot.setEnabled(val)
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

    @QtCore.Slot()
    def finished(self):
        self.raise_()
        QtWidgets.QMessageBox.information(
            self, "VTA video overlay", self.tr("Video processing completed")
        )
        self.set_stuff_enabled(True)
        self.progressbar.setValue(0)

    @QtCore.Slot(progress_tpl)
    def update_progressbar(self, tpl: progress_tpl):
        self.update_image(frame=tpl.frame)
        self.progressbar.setValue(tpl.progress)

    def update_image(self, frame: cv2.typing.MatLike | None):
        if frame is None:
            return
        self.video_preview.setPixmap(cv_to_pixmap(frame))

    @QtCore.Slot()
    def overlay(self):
        savepath = Path(pick_path_save())
        self.gui_to_data()
        if self.cb_trim.isChecked():
            start_timestamp = self.sb_trim.value()
        else:
            start_timestamp = 0.0
        log.info(self.tr("Operator: {operator}").format(operator=self.data.operator))
        log.info(self.tr("Sample: {sample}").format(sample=self.data.sample))
        log.info(
            self.tr("Temperature calibration enabled: {bool}").format(
                bool=self.data.temp_enabled
            )
        )
        log.info(
            self.tr("Polynomial coefficients: {coeff}").format(coeff=self.data.coeff)
        )
        log.info(f"Plot enabled: {self.cb_plot.isChecked()}")
        w = Worker(
            parent=self,
            video_file_path_input=Path(self.edit_video.text()),
            video_file_path_output=savepath,
            data=self.data,
            start_timestamp=start_timestamp,
            plot_enabled=self.cb_plot.isChecked(),
        )
        w.progress.connect(self.update_progressbar)
        w.finished.connect(self.finished)
        if self.cb_excel.isChecked():
            excelpath = Path(self.edit_tda.text()).with_suffix(".xlsx")
            self.data.to_excel(excelpath)
        self.set_stuff_enabled(False)
        w.start()
