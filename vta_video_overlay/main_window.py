import platform
import subprocess
import time
from dataclasses import replace
from pathlib import Path

from loguru import logger as log
from PySide6 import QtCore, QtGui, QtWidgets

from vta_video_overlay.__version__ import __version__
from vta_video_overlay.about_window import AboutWindow
from vta_video_overlay.config import appdata_path, config
from vta_video_overlay.controller import Controller
from vta_video_overlay.crop_selection_widgets import RectangleGeometry
from vta_video_overlay.data_collections import ProcessProgress, ProcessResult
from vta_video_overlay.ffmpeg_utils import FFmpeg
from vta_video_overlay.graph_preview_dialog import GraphPreviewDialog
from vta_video_overlay.enums import OverlapStatus
from vta_video_overlay.info_builders import (
    build_aligned_info,
    build_timeline_selection,
    build_video_info,
    update_video_info_with_timeline,
)
from vta_video_overlay.info_models import (
    SessionState,
    VideoInfo,
)
from vta_video_overlay.overlay_settings_dialog import OverlaySettingsDialog
from vta_video_overlay.aspect_ratio_label import AspectRatioLabel
from vta_video_overlay.preview_worker import PreviewWorker
from vta_video_overlay.session_info_widget import SessionInfoWidget
from vta_video_overlay.temp_dir_manager import TempDirManager
from vta_video_overlay.ui.MainWindow import Ui_MainWindow


def open_file_explorer(path: Path):
    system = platform.system()
    if system == "Windows":
        subprocess.Popen(["explorer", str(path)])
    elif system == "Linux":
        subprocess.Popen(["xdg-open", str(path)])
    else:
        print("Unsupported operating system")


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    video_preview: AspectRatioLabel
    session: SessionState

    # Сигналы для общения с воркером
    worker_data_signal = QtCore.Signal(object, object, object)  # data, crop_rect, timeline
    worker_request_signal = QtCore.Signal(int, object, object, object)  # frame_index, data, crop_rect, timeline

    def __init__(self, controller: Controller):
        super().__init__()
        self.setupUi(self)

        self.controller = controller
        self.controller.setParent(self)
        self.controller.crop_done.connect(self.crop_done)

        self.btn_tda.clicked.connect(self.pick_file)
        self.btn_tda.setToolTip(self.tr("Select measurement data file (.tda, .vtaz)"))
        self.btn_video.clicked.connect(self.pick_video)
        self.btn_video.setToolTip(self.tr("Select input video file"))
        self.btn_convert.clicked.connect(self.overlay)
        self.btn_convert.setEnabled(False)
        self.btn_convert.setToolTip(self.tr("Start video export with data overlay"))
        self.statusbar.addWidget(
            QtWidgets.QLabel(self.tr("Version: {v}").format(v=__version__))
        )

        # --- FPS & ETA LABELS ---
        self.fps_label = QtWidgets.QLabel("FPS: --")
        self.fps_label.setFixedWidth(80)
        self.fps_label.hide()
        self.statusbar.addPermanentWidget(self.fps_label)

        self.eta_label = QtWidgets.QLabel("Elapsed: 00:00 | ETA: --:--")
        self.eta_label.setFixedWidth(220)
        self.eta_label.hide()
        self.statusbar.addPermanentWidget(self.eta_label)

        self.render_start_time: float | None = None
        self.current_render_fps: float = 0.0

        self.controller.pipeline.stage_progress.connect(self.update_progressbar)
        self.controller.pipeline.stage_finished.connect(self.stage_finished)
        self.controller.pipeline.fps_updated.connect(self.update_fps)
        self.controller.pipeline.work_finished.connect(self.finished)

        self.about_window = AboutWindow(parent=self)

        # System tray для уведомлений
        self.tray_icon = QtWidgets.QSystemTrayIcon(self)
        self.tray_icon.setIcon(QtGui.QIcon(":/assets/icon.png"))

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

        self.reset_crop_action = QtGui.QAction(self.tr("Reset Crop"), self)
        self.reset_crop_action.triggered.connect(self.reset_crop)
        self.reset_crop_action.setEnabled(False)
        self.menubar.addAction(self.reset_crop_action)

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

        # Экшен настройки элементов наложения
        self.actionOverlaySettings = QtGui.QAction(self.tr("Overlay Settings..."), self)
        self.actionOverlaySettings.triggered.connect(self.show_overlay_settings)
        self.menuOptions.addAction(self.actionOverlaySettings)

        # --- СОСТОЯНИЕ СВЕДЕНИЙ СЕССИИ ---
        self.session = SessionState()

        # --- НАСТРОЙКА UI ПРЕДПРОСМОТРА ---

        # 1. Слайдер
        self.slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setEnabled(False)

        self.slider.valueChanged.connect(self.handle_slider_moved)
        self.slider.sliderReleased.connect(self.handle_slider_released)

        self.lbl_time = QtWidgets.QLabel("0.0s")
        self.lbl_time.setFixedWidth(50)
        self.lbl_time.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)

        # 2. Стек для переключения Картинка / Загрузка
        self.preview_stack = QtWidgets.QStackedWidget()

        self.video_preview = AspectRatioLabel()
        self.video_preview.setStyleSheet("background-color: rgb(0, 0, 0);")
        self.preview_stack.addWidget(self.video_preview)

        loading_widget = QtWidgets.QWidget()
        loading_layout = QtWidgets.QVBoxLayout(loading_widget)
        loading_bar = QtWidgets.QProgressBar()
        loading_bar.setRange(0, 0)
        loading_bar.setTextVisible(False)
        loading_label = QtWidgets.QLabel(self.tr("Rendering preview..."))
        loading_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        loading_layout.addStretch()
        loading_layout.addWidget(loading_label)
        loading_layout.addWidget(loading_bar)
        loading_layout.addStretch()
        self.preview_stack.addWidget(loading_widget)

        # Создаём новый центральный layout
        central = QtWidgets.QWidget()
        main_grid = QtWidgets.QGridLayout(central)
        main_grid.setContentsMargins(4, 4, 4, 4)
        main_grid.setSpacing(6)

        # --- Левый верхний блок: управление ---
        control_widget = QtWidgets.QWidget()
        control_layout = QtWidgets.QVBoxLayout(control_widget)
        control_layout.setContentsMargins(0, 0, 0, 0)

        tda_row = QtWidgets.QHBoxLayout()
        tda_row.addWidget(self.btn_tda)
        tda_row.addWidget(self.edit_tda)
        control_layout.addLayout(tda_row)

        video_row = QtWidgets.QHBoxLayout()
        video_row.addWidget(self.btn_video)
        video_row.addWidget(self.edit_video)
        control_layout.addLayout(video_row)

        control_layout.addWidget(self.cb_excel)
        control_layout.addWidget(self.btn_convert)
        control_layout.addStretch()
        control_layout.addWidget(self.progressbar)

        main_grid.addWidget(control_widget, 0, 0)

        # --- Правый верхний блок: preview ---
        preview_container = QtWidgets.QWidget()
        preview_layout = QtWidgets.QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.addWidget(self.preview_stack)

        slider_layout = QtWidgets.QHBoxLayout()
        slider_layout.addWidget(self.lbl_time)
        slider_layout.addWidget(self.slider)
        preview_layout.addLayout(slider_layout)

        main_grid.addWidget(preview_container, 0, 1)

        # --- Нижний блок: три информационных панели ---
        self.session_info = SessionInfoWidget()
        self.session_info.setMinimumHeight(200)
        main_grid.addWidget(self.session_info, 1, 0, 1, 2)

        main_grid.setRowStretch(0, 1)
        main_grid.setRowStretch(1, 1)
        main_grid.setColumnStretch(0, 1)
        main_grid.setColumnStretch(1, 1)

        # Заменяем дефолтный centralwidget из .ui динамической сеткой.
        # Замечание: widget_container и line из .ui не используются напрямую в новом layout.
        self.setCentralWidget(central)

        # Потоки
        self.preview_thread: QtCore.QThread | None = None
        self.worker: PreviewWorker | None = None
        self.current_fps: float = 30.0
        self.preview_total_frames: int = 0

    def _warn(self, text: str) -> None:
        QtWidgets.QMessageBox.warning(self, self.tr("Warning"), text)

    def start_preview_worker(self, video_path: str, video_info: VideoInfo | None = None):
        """Запускает поток предпросмотра."""
        if self.worker is not None:
            try:
                self.worker_data_signal.disconnect(self.worker.update_data)
            except (RuntimeError, TypeError):
                pass
            try:
                self.worker_request_signal.disconnect(self.worker.request_frame)
            except (RuntimeError, TypeError):
                pass
            try:
                self.worker.frame_ready.disconnect(self.handle_frame_ready)
            except (RuntimeError, TypeError):
                pass

        if self.preview_thread is not None:
            self.preview_thread.quit()
            self.preview_thread.wait()
            self.preview_thread.deleteLater()
            self.preview_thread = None

        if self.worker is not None:
            self.worker.deleteLater()
            self.worker = None

        self.preview_thread = QtCore.QThread(self)
        self.worker = PreviewWorker(video_path)
        self.worker.moveToThread(self.preview_thread)

        self.preview_thread.started.connect(self.worker.init_video)
        self.worker_data_signal.connect(self.worker.update_data)
        self.worker_request_signal.connect(self.worker.request_frame)
        self.worker.frame_ready.connect(self.handle_frame_ready)

        self.preview_thread.start()

        if video_info is not None:
            self.preview_total_frames = max(0, video_info.total_frames)
            self.current_fps = video_info.fps_nominal if video_info.fps_nominal > 0 else 30.0

        self.slider.setValue(0)
        self._refresh_slider_range()
        self.update_worker_data()
        self.request_preview_update(0)

    def update_worker_data(self):
        """Отправляет данные в воркер."""
        data = self.controller.pipeline.data
        if self.worker:
            crop_rect = self.controller.pipeline.crop_rect
            timeline = self.controller.pipeline.timeline
            self.worker_data_signal.emit(data, crop_rect, timeline)

    def request_preview_update(self, frame_index):
        """Запрашивает обновление кадра."""
        if not self.worker:
            return

        self.preview_stack.setCurrentIndex(1)

        data = self.controller.pipeline.data
        crop_rect = self.controller.pipeline.crop_rect
        timeline = self.controller.pipeline.timeline
        self.worker_request_signal.emit(frame_index, data, crop_rect, timeline)

    @QtCore.Slot(object, float)
    def handle_frame_ready(self, pixmap, time_sec):
        """Пришел готовый кадр из потока."""
        self.video_preview.setPixmap(pixmap)
        self.lbl_time.setText(f"{time_sec:.1f}s")
        self.preview_stack.setCurrentIndex(0)

    @QtCore.Slot(int)
    def handle_slider_moved(self, val):
        """Показывает absolute source time для kept-позиции."""
        timeline = self.controller.pipeline.timeline
        if timeline is not None and timeline.status is not OverlapStatus.NONE:
            if val < len(timeline.kept_timestamps_sec):
                t = float(timeline.kept_timestamps_sec[val])
                self.lbl_time.setText(f"{t:.1f}s")
            else:
                self.lbl_time.setText("—")
        elif self.current_fps > 0:
            self.lbl_time.setText(f"{val / self.current_fps:.1f}s")

    @QtCore.Slot()
    def handle_slider_released(self):
        """Слайдер отпустили: запрашиваем рендер финального положения."""
        val = self.slider.value()
        self.request_preview_update(val)

    def overlay(self):
        timeline = self.controller.pipeline.timeline
        if timeline is None or timeline.status is OverlapStatus.NONE:
            self._warn(
                self.tr("No temporal overlap between video and data. Export is not possible.")
            )
            return

        self.set_stuff_enabled(False)
        convert_excel = self.cb_excel.isChecked()
        self.render_start_time = time.perf_counter()
        self.current_render_fps = 0.0
        self.fps_label.show()
        self.eta_label.show()
        self.eta_label.setText("Elapsed: 00:00 | ETA: --:--")
        log.info(self.tr("Started video processing"))
        self.controller.overlay(convert_excel=convert_excel)

    def _refresh_slider_range(self):
        """Обновляет диапазон слайдера на основе timeline selection."""
        timeline = self.controller.pipeline.timeline
        if timeline is not None and timeline.status is not OverlapStatus.NONE:
            self.slider.setRange(0, max(0, timeline.kept_frames - 1))
            self.slider.setEnabled(True)
        elif self.preview_total_frames > 0:
            self.slider.setRange(0, max(0, self.preview_total_frames - 1))
            self.slider.setEnabled(True)
        else:
            self.slider.setRange(0, 0)
            self.slider.setEnabled(False)

    def _refresh_timeline_and_aligned(self) -> None:
        """Пересчитывает timeline selection и aligned info."""
        if self.session.measurement is None or self.session.video_info is None:
            self.session.timeline = None
            self.session.aligned_info = None
            self.btn_convert.setEnabled(False)
            return

        timeline = build_timeline_selection(
            data=self.session.measurement.data,
            video_info=self.session.video_info,
        )
        self.session.timeline = timeline
        self.session.video_info = update_video_info_with_timeline(
            self.session.video_info,
            timeline,
        )
        self.session.aligned_info = build_aligned_info(
            data=self.session.measurement.data,
            video_info=self.session.video_info,
            timeline=timeline,
        )
        self.controller.pipeline.timeline = self.session.timeline

        has_valid_overlap = timeline.status is not OverlapStatus.NONE
        self.btn_convert.setEnabled(has_valid_overlap)

        self._refresh_slider_range()

    def _refresh_info_panel(self) -> None:
        self.session_info.set_measurement_info(
            self.session.measurement.info if self.session.measurement else None
        )
        self.session_info.set_video_info(self.session.video_info)
        self.session_info.set_aligned_info(self.session.aligned_info)

    @QtCore.Slot()
    def reset_crop(self):
        """Сбрасывает кроп к оригинальному разрешению видео."""
        self.controller.pipeline.crop_rect = None

        if self.session.video_info is not None:
            self.session.video_info = replace(self.session.video_info, crop_rect=None)
            self.video_preview.set_aspect_ratio(
                self.session.video_info.input_width,
                self.session.video_info.input_height,
            )
            self._refresh_timeline_and_aligned()
            self._refresh_info_panel()

        self.update_worker_data()
        if self.slider.isEnabled():
            self.request_preview_update(self.slider.value())

        self.reset_crop_action.setEnabled(False)
        log.info("Crop reset to original resolution")

    @QtCore.Slot()
    def crop_done(self, rect: RectangleGeometry):
        video_path = self.controller.pipeline.video_path_input
        if video_path and Path(video_path).is_file():
            try:
                ff = FFmpeg()
                vw, vh = ff.get_resolution(Path(video_path))
                rect = rect.safe_bound(vw, vh)
            except Exception as e:
                log.warning(f"Could not get resolution for crop bounding: {e}")
        log.info(self.tr("Crop done: {xywh}").format(xywh=rect))
        if rect and rect.h > 0:
            self.video_preview.set_aspect_ratio(rect.w, rect.h)

        if self.session.video_info is not None:
            if rect is None:
                self.session.video_info = replace(self.session.video_info, crop_rect=None)
                self.video_preview.set_aspect_ratio(
                    self.session.video_info.input_width,
                    self.session.video_info.input_height,
                )
            else:
                self.session.video_info = replace(self.session.video_info, crop_rect=rect)
            self._refresh_info_panel()

        self.reset_crop_action.setEnabled(True)

        if self.slider.isEnabled():
            self.request_preview_update(self.slider.value())

    @QtCore.Slot()
    def pick_file(self):
        loaded = self.controller.pick_file()
        if loaded is not None:
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.CursorShape.WaitCursor)
            self.session.measurement = loaded
            data = loaded.data

            log.info(self.tr("Selected data file: {path}").format(path=data.path))
            self.edit_tda.setText(str(data.path))

            self._refresh_timeline_and_aligned()
            self._refresh_info_panel()

            self.update_worker_data()
            if self.slider.isEnabled():
                self.request_preview_update(self.slider.value())
            if QtWidgets.QApplication.overrideCursor() is not None:
                QtWidgets.QApplication.restoreOverrideCursor()

    @QtCore.Slot()
    def pick_video(self):
        res = self.controller.pick_video()
        if not res:
            return
        path, size = res
        video_path = Path(path)

        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.CursorShape.WaitCursor)
        log.info(self.tr("Selected video: {path}").format(path=path))
        self.edit_video.setText(str(path))
        self.crop_action.setEnabled(True)

        # Сброс crop от предыдущего видео
        self.controller.pipeline.crop_rect = None
        self.reset_crop_action.setEnabled(False)

        if size[1] > 0:
            self.video_preview.set_aspect_ratio(size[0], size[1])

        self.session.video_info = build_video_info(
            video_path=video_path,
            crop_rect=self.controller.pipeline.crop_rect,
        )

        self.start_preview_worker(path, self.session.video_info)
        self._refresh_timeline_and_aligned()
        self._refresh_info_panel()
        if QtWidgets.QApplication.overrideCursor() is not None:
            QtWidgets.QApplication.restoreOverrideCursor()

    @QtCore.Slot()
    def show_about(self):
        self.about_window.show()
        self.about_window.raise_()

    def set_stuff_enabled(self, val: bool):
        self.btn_tda.setEnabled(val)
        self.btn_video.setEnabled(val)
        self.edit_tda.setEnabled(val)
        self.edit_video.setEnabled(val)
        self.cb_excel.setEnabled(val)
        self.crop_action.setEnabled(val)
        self.reset_crop_action.setEnabled(val and self.controller.pipeline.crop_rect is not None)
        self.slider.setEnabled(val)
        if val:
            # Восстанавливаем btn_convert по состоянию timeline
            timeline = self.controller.pipeline.timeline
            self.btn_convert.setEnabled(
                timeline is not None and timeline.status is not OverlapStatus.NONE
            )
        else:
            self.btn_convert.setEnabled(False)

    @QtCore.Slot(float)
    def update_fps(self, fps: float):
        """Обновляет отображение FPS и расчёт ETA в статусбаре."""
        self.fps_label.setText(f"FPS: {fps:.1f}")
        self.current_render_fps = fps
        self._update_eta_display()

    def finished(self, tpl: ProcessResult):
        self.raise_()
        self.render_start_time = None
        self.current_render_fps = 0.0
        self.fps_label.hide()
        self.eta_label.hide()
        self.progressbar.setFormat("%p%")
        if tpl.is_success:
            self._show_notification(
                self.tr("Video processing completed"),
                self.tr("Export finished successfully."),
            )
            QtWidgets.QApplication.processEvents()
            QtWidgets.QMessageBox.information(
                self, "VTA video overlay", self.tr("Video processing completed")
            )
        else:
            log.error(tpl.traceback_msg)
            self._show_notification(
                self.tr("Video processing failed"),
                self.tr("An error occurred during export."),
            )
            QtWidgets.QApplication.processEvents()
            QtWidgets.QMessageBox.critical(
                self,
                self.tr("Error"),
                self.tr(
                    "Video processing failed.\nException occurred.\n\n{msg}"
                ).format(msg=tpl.traceback_msg),
            )
        TempDirManager.cleanup()
        self.set_stuff_enabled(True)
        self.progressbar.setValue(0)

    def _show_notification(self, title: str, message: str) -> None:
        """Показывает системное уведомление (toast) через QSystemTrayIcon."""
        if not QtWidgets.QSystemTrayIcon.isSystemTrayAvailable():
            return
        if not self.tray_icon.isVisible():
            self.tray_icon.show()
        self.tray_icon.showMessage(
            title,
            message,
            QtWidgets.QSystemTrayIcon.MessageIcon.Information,
            5000,  # ms
        )

    def update_progressbar(self, progress: ProcessProgress):
        """Обновляет прогрессбар, ETA и превью во время рендера."""
        self.progressbar.setValue(progress.value)
        self._update_eta_display()

        if progress.frame is not None:
            if self.preview_stack.currentIndex() != 0:
                self.preview_stack.setCurrentIndex(0)

            self.video_preview.setPixmap(progress.frame.to_pixmap())

    def _update_eta_display(self):
        if self.render_start_time is None:
            return

        elapsed_sec = time.perf_counter() - self.render_start_time
        elapsed_str = f"{int(elapsed_sec // 60):02d}:{int(elapsed_sec % 60):02d}"

        current_idx = self.progressbar.value()
        max_idx = self.progressbar.maximum()
        remaining_frames = max_idx - current_idx

        if self.current_render_fps > 0 and remaining_frames > 0:
            eta_sec = remaining_frames / self.current_render_fps
            eta_str = f"{int(eta_sec // 60):02d}:{int(eta_sec % 60):02d}"
        else:
            eta_str = "--:--"

        self.eta_label.setText(f"Elapsed: {elapsed_str} | ETA: {eta_str}")
        if max_idx > 0:
            pct = int((current_idx / max_idx) * 100)
            self.progressbar.setFormat(f"{pct}% ({elapsed_str} / ETA {eta_str})")

    def stage_finished(self, tpl):
        total, stage_str, unit = tpl
        self.progressbar.setValue(0)
        self.progressbar.setMaximum(total)

    @QtCore.Slot(bool)
    def toggle_graph_enabled(self, checked: bool):
        config.graph.enabled = checked
        config.update()
        log.info(f"Graph enabled: {checked}")
        self.update_worker_data()
        if self.slider.isEnabled():
            self.request_preview_update(self.slider.value())

    @QtCore.Slot()
    def show_graph_preview(self):
        data = self.controller.pipeline.data
        if data is None:
            self._warn(self.tr("Please load data first."))
            return

        if data.speed is None:
            self._warn(self.tr("No speed data available."))
            return

        dlg = GraphPreviewDialog(data.time, data.speed, parent=self)
        dlg.exec()

    @QtCore.Slot()
    def show_overlay_settings(self):
        dlg = OverlaySettingsDialog(parent=self)
        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self.actionGraphEnabled.setChecked(config.graph.enabled)
            # Пересоздать renderer с новыми настройками
            self.update_worker_data()
            if self.slider.isEnabled():
                self.request_preview_update(self.slider.value())

    def closeEvent(self, event):
        pipeline = self.controller.pipeline
        if pipeline and pipeline.isRunning():
            log.info("Closing window: stopping pipeline...")
            pipeline.stop()
            if not pipeline.wait(10000):
                log.error("Pipeline did not stop in time, terminating...")
                pipeline.terminate()
                pipeline.wait(2000)

        if self.preview_thread and self.preview_thread.isRunning():
            if self.worker:
                QtCore.QMetaObject.invokeMethod(
                    self.worker, "cleanup", QtCore.Qt.ConnectionType.QueuedConnection  # type: ignore[call-overload]
                )
            self.preview_thread.quit()
            self.preview_thread.wait(3000)
        super().closeEvent(event)
        QtWidgets.QApplication.quit()
