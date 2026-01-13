import platform
import subprocess
from pathlib import Path

import cv2
from loguru import logger as log
from PySide6 import QtCore, QtGui, QtWidgets

from vta_video_overlay.__version__ import __version__
from vta_video_overlay.about_window import AboutWindow
from vta_video_overlay.config import appdata_path, config
from vta_video_overlay.controller import Controller
from vta_video_overlay.crop_selection_widgets import RectangleGeometry
from vta_video_overlay.data_collections import ProcessProgress, ProcessResult
from vta_video_overlay.data_file import Data
from vta_video_overlay.file_widget_base import FileDataWidgetBase
from vta_video_overlay.graph_preview_dialog import GraphPreviewDialog
from vta_video_overlay.preview_worker import PreviewWorker
from vta_video_overlay.temp_dir_manager import TempDirManager
from vta_video_overlay.ui.MainWindow import Ui_MainWindow


def open_file_explorer(path: Path):
    system = platform.system()
    if system == "Windows":
        subprocess.Popen(["explorer", path], shell=True)
    elif system == "Linux":
        subprocess.Popen(["xdg-open", path])
    else:
        print("Unsupported operating system")


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    # Сигналы для общения с воркером
    worker_data_signal = QtCore.Signal(object, object)  # data, crop_rect
    worker_request_signal = QtCore.Signal(int, object, object)  # frame_index, data, crop_rect

    def __init__(self, controller: Controller):
        super().__init__()
        self.setupUi(self)

        self.controller = controller
        self.controller.setParent(self)
        self.controller.crop_done.connect(self.crop_done)

        self.btn_tda.clicked.connect(self.pick_file)
        self.btn_video.clicked.connect(self.pick_video)
        self.btn_convert.clicked.connect(self.overlay)
        self.statusbar.addWidget(
            QtWidgets.QLabel(self.tr("Version: {v}").format(v=__version__))
        )
        
        # --- FPS LABEL ---
        self.fps_label = QtWidgets.QLabel("FPS: --")
        self.fps_label.setFixedWidth(80)
        self.statusbar.addPermanentWidget(self.fps_label)
        
        self.about_window = AboutWindow(parent=self)
        self.actionAbout = QtGui.QAction(self.tr("About"), self)
        self.actionAbout.triggered.connect(self.show_about)
        self.menubar.addAction(self.actionAbout)

        self.explorer_action = QtGui.QAction(self.tr("Open config folder"), self)
        self.explorer_action.triggered.connect(lambda: open_file_explorer(appdata_path))
        self.menubar.addAction(self.explorer_action)

        self.crop_action = QtGui.QAction(self.tr("Crop"), self)
        self.crop_action.triggered.connect(self.controller.crop)
        self.crop_action.setEnabled(False)
        self.menubar.addAction(self.crop_action)

        # Добавляем меню Options
        self.menuOptions = self.menubar.addMenu(self.tr("Options"))
        
        # Чекбокс включения графика
        self.actionGraphEnabled = QtGui.QAction(self.tr("Show Speed Graph"), self)
        self.actionGraphEnabled.setCheckable(True)
        self.actionGraphEnabled.setChecked(config.graph.enabled)
        self.actionGraphEnabled.triggered.connect(self.toggle_graph_enabled)
        self.menuOptions.addAction(self.actionGraphEnabled)
        
        # Экшен предпросмотра графика
        self.actionPreviewGraph = QtGui.QAction(self.tr("Preview Graph Window"), self)
        self.actionPreviewGraph.triggered.connect(self.show_graph_preview)
        self.menuOptions.addAction(self.actionPreviewGraph)

        # --- НАСТРОЙКА UI ПРЕДПРОСМОТРА ---
        
        # 1. Слайдер
        self.slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setEnabled(False)
        
        # Подключаем вручную, избегая имен on_... для слотов, чтобы не путать connectSlotsByName
        self.slider.valueChanged.connect(self.handle_slider_moved)
        self.slider.sliderReleased.connect(self.handle_slider_released)

        self.lbl_time = QtWidgets.QLabel("0.0s")
        self.lbl_time.setFixedWidth(50)
        self.lbl_time.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)

        slider_layout = QtWidgets.QHBoxLayout()
        slider_layout.addWidget(self.lbl_time)
        slider_layout.addWidget(self.slider)

        # 2. Стек для переключения Картинка / Загрузка
        self.preview_stack = QtWidgets.QStackedWidget()
        
        # Стр 0: Видео (берем существующий виджет)
        # Важно: video_preview уже создан в setupUi, но мы его переносим в stack
        self.video_preview.setScaledContents(True)
        self.preview_stack.addWidget(self.video_preview)
        
        # Стр 1: Загрузка
        loading_widget = QtWidgets.QWidget()
        loading_layout = QtWidgets.QVBoxLayout(loading_widget)
        loading_bar = QtWidgets.QProgressBar()
        loading_bar.setRange(0, 0)  # Бесконечная анимация
        loading_bar.setTextVisible(False)
        loading_label = QtWidgets.QLabel(self.tr("Rendering preview..."))
        loading_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        loading_layout.addStretch()
        loading_layout.addWidget(loading_label)
        loading_layout.addWidget(loading_bar)
        loading_layout.addStretch()
        self.preview_stack.addWidget(loading_widget)

        # 3. Внедрение в лейаут
        # Мы заменяем место, где лежал video_preview, на наш контейнер со стеком и слайдером
        grid = self.centralwidget.layout()
        if grid and isinstance(grid, QtWidgets.QGridLayout):
            # Находим, где лежит video_preview
            # Примечание: после addWidget в стек, виджет может пропасть из грида,
            # но позицию мы должны знать заранее или использовать хардкод из .ui (row=0, col=3, rowSpan=7)
            # В MainWindow.ui video_preview лежит в gridLayout по координатам 0, 3, 7, 1
            
            preview_container = QtWidgets.QWidget()
            vbox = QtWidgets.QVBoxLayout(preview_container)
            vbox.setContentsMargins(0, 0, 0, 0)
            vbox.addWidget(self.preview_stack)
            vbox.addLayout(slider_layout)
            
            # Удаляем старый плейсхолдер (хотя он уже перемещен в стек, но слот в лейауте может быть занят)
            # Просто кладем поверх или заменяем
            grid.addWidget(preview_container, 0, 3, 7, 1)
        else:
            log.error("Central widget layout is not QGridLayout or not found")

        # Потоки
        self.preview_thread: QtCore.QThread | None = None
        self.worker: PreviewWorker | None = None
        self.current_fps: float = 30.0
        self.preview_total_frames: int = 0

    def start_preview_worker(self, video_path):
        """Запускает поток предпросмотра."""
        # Очистка старого потока
        if self.preview_thread:
            self.preview_thread.quit()
            self.preview_thread.wait()

        self.preview_thread = QtCore.QThread()
        self.worker = PreviewWorker(video_path)
        self.worker.moveToThread(self.preview_thread)

        # Подключение сигналов (только воркер-специфичные)
        self.preview_thread.started.connect(self.worker.init_video)
        self.worker_data_signal.connect(self.worker.update_data)
        self.worker_request_signal.connect(self.worker.request_frame)
        self.worker.frame_ready.connect(self.handle_frame_ready)
        
        # Запуск
        self.preview_thread.start()

        # Узнаем кол-во кадров синхронно (один раз для слайдера)
        cap = cv2.VideoCapture(video_path)
        if cap.isOpened():
            self.preview_total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.current_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            self.slider.setRange(0, max(0, self.preview_total_frames - 1))
            self.slider.setValue(0)
            self.slider.setEnabled(True)
            cap.release()

        # Инициализация данных (если они уже были загружены)
        self.update_worker_data()
        
        # Запрос первого кадра
        self.request_preview_update(0)

    def update_worker_data(self):
        """Отправляет данные в воркер."""
        data = self.controller.pipeline.data
        if self.worker:
            crop_rect = self.controller.pipeline.crop_rect
            self.worker_data_signal.emit(data, crop_rect)

    def request_preview_update(self, frame_index):
        """Запрашивает обновление кадра."""
        if not self.worker:
            return
        
        # Показываем лоадер
        self.preview_stack.setCurrentIndex(1)
        
        data = self.controller.pipeline.data
        crop_rect = self.controller.pipeline.crop_rect
        self.worker_request_signal.emit(frame_index, data, crop_rect)

    @QtCore.Slot(object, float)
    def handle_frame_ready(self, pixmap, time_sec):
        """Пришел готовый кадр из потока."""
        self.video_preview.setPixmap(pixmap)
        self.lbl_time.setText(f"{time_sec:.1f}s")
        self.preview_stack.setCurrentIndex(0)  # Показываем картинку

    @QtCore.Slot(int)
    def handle_slider_moved(self, val):
        """Слайдер тянут: обновляем только текст времени (быстро)."""
        if self.current_fps > 0:
            self.lbl_time.setText(f"{val / self.current_fps:.1f}s")

    @QtCore.Slot()
    def handle_slider_released(self):
        """Слайдер отпустили: запускаем рендер."""
        val = self.slider.value()
        self.request_preview_update(val)

    def overlay(self):
        self.set_stuff_enabled(False)
        convert_excel = self.cb_excel.isChecked()
        self.controller.pipeline.stage_progress.connect(self.update_progressbar)
        self.controller.pipeline.stage_finished.connect(self.stage_finished)
        self.controller.pipeline.fps_updated.connect(self.update_fps)
        self.controller.pipeline.work_finished.disconnect()
        self.controller.pipeline.work_finished.connect(self.finished)
        log.info(self.tr("Started video processing"))
        self.controller.overlay(convert_excel=convert_excel)

    @QtCore.Slot()
    def crop_done(self, rect: RectangleGeometry):
        log.info(self.tr("Crop done: {xywh}").format(xywh=rect))
        # Масштабируем ширину превью пропорционально новому кропу
        # h фиксированная, w меняется
        if rect.h > 0:
            current_h = self.preview_stack.height()
            ratio = rect.w / rect.h
            new_w = int(current_h * ratio)
            # Ограничим разумными пределами
            new_w = max(200, min(new_w, 800))
            self.video_preview.setMinimumWidth(new_w)
        
        # Обновляем превью
        if self.slider.isEnabled():
            self.request_preview_update(self.slider.value())

    @QtCore.Slot()
    def pick_file(self):
        result = self.controller.pick_file()
        if result is not None:
            data, widget = result
            log.info(self.tr("Selected tda file: {path}").format(path=data.path))
            
            self.data_to_gui(data=data, widget=widget)
            
            # Обновляем воркер новыми данными
            self.update_worker_data()
            # Обновляем текущий кадр (чтобы появился оверлей, если видео уже загружено)
            if self.slider.isEnabled():
                self.request_preview_update(self.slider.value())

    @QtCore.Slot()
    def pick_video(self):
        res = self.controller.pick_video()
        if not res:
            return
        path, size = res
        
        log.info(self.tr("Selected video: {path}").format(path=path))
        self.edit_video.setText(str(path))
        self.crop_action.setEnabled(True)
        
        # Настраиваем размеры превью (сохраняем аспект)
        h = 400 # Целевая высота
        if size[1] > 0:
            w = int(size[0] * h / size[1])
            self.video_preview.setMinimumHeight(h)
            self.video_preview.setMinimumWidth(w)

        # Запускаем воркер
        self.start_preview_worker(path)

    @QtCore.Slot()
    def show_about(self):
        self.about_window.show()
        self.about_window.raise_()

    def set_stuff_enabled(self, val: bool):
        self.btn_tda.setEnabled(val)
        self.btn_video.setEnabled(val)
        self.btn_convert.setEnabled(val)
        self.edit_tda.setEnabled(val)
        self.edit_video.setEnabled(val)
        self.cb_excel.setEnabled(val)
        self.crop_action.setEnabled(val)
        self.slider.setEnabled(val)

    def data_to_gui(self, data: Data, widget: FileDataWidgetBase):
        self.edit_tda.setText(str(data.path))

        container_layout = self.widget_container.layout()
        if container_layout is None:
            container_layout = QtWidgets.QVBoxLayout(self.widget_container)
            container_layout.setContentsMargins(0, 0, 0, 0)
        else:
            while child := container_layout.takeAt(0):
                if widget_child := child.widget():
                    widget_child.deleteLater()

        if widget:
            container_layout.addWidget(widget)

    @QtCore.Slot(float)
    def update_fps(self, fps: float):
        """Обновляет отображение FPS в статусбаре."""
        self.fps_label.setText(f"FPS: {fps:.1f}")

    def finished(self, tpl: ProcessResult):
        self.raise_()
        self.fps_label.setText("FPS: --")  # Сброс FPS
        if tpl.is_success:
            QtWidgets.QMessageBox.information(
                self, "VTA video overlay", self.tr("Video processing completed")
            )
        else:
            log.error(tpl.traceback_msg)
            QtWidgets.QMessageBox.critical(
                self,
                self.tr("Error"),
                self.tr(
                    f"Video processing failed.\nException occurred.\n\n{tpl.traceback_msg}"
                ),
            )
        TempDirManager.cleanup()
        self.set_stuff_enabled(True)
        self.progressbar.setValue(0)

    def update_progressbar(self, progress: ProcessProgress):
        """Обновляет прогрессбар и превью во время рендера."""
        self.progressbar.setValue(progress.value)
        
        # Если кадр передан, показываем его в превью
        if progress.frame is not None:
            # Убедимся, что показываем слой с картинкой (а не лоадер)
            if self.preview_stack.currentIndex() != 0:
                self.preview_stack.setCurrentIndex(0)
                
            self.video_preview.setPixmap(progress.frame.to_pixmap())

    def stage_finished(self, tpl):
        total, stage_str, unit = tpl
        self.progressbar.setValue(0)
        self.progressbar.setMaximum(total)

    @QtCore.Slot(bool)
    def toggle_graph_enabled(self, checked: bool):
        config.graph.enabled = checked
        log.info(f"Graph enabled: {checked}")
        if self.slider.isEnabled():
            self.request_preview_update(self.slider.value())

    @QtCore.Slot()
    def show_graph_preview(self):
        data = self.controller.pipeline.data
        if data is None:
             QtWidgets.QMessageBox.warning(self, self.tr("Warning"), self.tr("Please load data first."))
             return
             
        # Свойство speed вызовет calculate_speed() автоматически при необходимости
        if data.speed is None:
             QtWidgets.QMessageBox.warning(self, self.tr("Warning"), self.tr("No speed data available."))
             return

        dlg = GraphPreviewDialog(data.time, data.speed, parent=self)
        dlg.exec()

    def closeEvent(self, event):
        if self.preview_thread:
            if self.worker:
                self.worker.cleanup()
            self.preview_thread.quit()
            self.preview_thread.wait()
        super().closeEvent(event)
