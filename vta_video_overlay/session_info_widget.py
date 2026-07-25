from PySide6 import QtCore, QtWidgets

from vta_video_overlay.info_models import AlignedInfo, MeasurementInfo, VideoInfo


class InfoPanel(QtWidgets.QGroupBox):
    """Один блок сведений с key-value списком и warning-областью."""

    def __init__(self, title: str, parent=None):
        super().__init__(title, parent)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        self.warning_label = QtWidgets.QLabel()
        self.warning_label.setStyleSheet("color: #cc7700; font-weight: bold;")
        self.warning_label.setWordWrap(True)
        self.warning_label.setMaximumHeight(80)
        self.warning_label.hide()
        layout.addWidget(self.warning_label)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)

        self.content = QtWidgets.QWidget()
        self.form = QtWidgets.QFormLayout(self.content)
        self.form.setContentsMargins(0, 0, 0, 0)
        self.form.setSpacing(3)

        scroll.setWidget(self.content)
        layout.addWidget(scroll)

    def set_warning(self, text: str | None):
        if text:
            self.warning_label.setText(f"⚠ {text}")
            self.warning_label.show()
        else:
            self.warning_label.hide()

    def set_rows(self, rows: list[tuple[str, str]]):
        while self.form.rowCount():
            self.form.removeRow(0)

        for key, value in rows:
            val_label = QtWidgets.QLabel(value)
            val_label.setWordWrap(True)
            val_label.setTextInteractionFlags(
                QtCore.Qt.TextInteractionFlag.TextSelectableByMouse
            )
            self.form.addRow(key, val_label)


class SessionInfoWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.panel_measurement = InfoPanel(self.tr("VTA / Data"))
        self.panel_video = InfoPanel(self.tr("Video"))
        self.panel_aligned = InfoPanel(self.tr("Aligned"))

        layout.addWidget(self.panel_measurement, 1)
        layout.addWidget(self.panel_video, 1)
        layout.addWidget(self.panel_aligned, 1)

    def set_measurement_info(self, info: MeasurementInfo | None) -> None:
        if info is None:
            self.panel_measurement.set_rows([(self.tr("Status"), self.tr("No data loaded"))])
            self.panel_measurement.set_warning(None)
            return

        self.panel_measurement.set_warning(None)
        self.panel_measurement.set_rows([
            (self.tr("Format"), info.source_format),
            (self.tr("Version"), info.version),
            (self.tr("Path"), str(info.path)),
            (self.tr("Sample"), info.sample),
            (self.tr("Operator"), info.operator),
            (self.tr("Points"), str(info.points)),
            (self.tr("Time range (s)"), f"{info.t_min_sec:.3f} — {info.t_max_sec:.3f}"),
            (self.tr("Duration (s)"), f"{info.duration_sec:.3f}"),
            (self.tr("EMF range (mV)"),
             "—" if info.emf_min is None else f"{info.emf_min:.3f} — {info.emf_max:.3f}"),
            (self.tr("Temperature"),
             self.tr("Yes") if info.temp_available else self.tr("No")),
            (self.tr("Temp range (°C)"),
             "—" if info.temp_min is None else f"{info.temp_min:.1f} — {info.temp_max:.1f}"),
            (self.tr("Calibration"), info.calibration_type or "—"),
            (self.tr("Semantics"), info.calibration_semantics or "—"),
            (self.tr("Cal. coefficients"), info.calibration_coeffs_text or "—"),
            (self.tr("TC coefficients"), info.thermocouple_coeffs_text or "—"),
            (self.tr("CJC"), info.cjc_text or "—"),
        ])

    def set_video_info(self, info: VideoInfo | None) -> None:
        if info is None:
            self.panel_video.set_rows([(self.tr("Status"), self.tr("No video loaded"))])
            self.panel_video.set_warning(None)
            return

        crop_text = (
            f"{info.crop_rect.x}, {info.crop_rect.y}, "
            f"{info.crop_rect.w}, {info.crop_rect.h}"
            if info.crop_rect else "—"
        )

        rows = [
            (self.tr("Path"), str(info.path)),
            (self.tr("Input size"), f"{info.input_width} × {info.input_height}"),
            (self.tr("Output size"), f"{info.output_width} × {info.output_height}"),
            (self.tr("Crop rect"), crop_text),
            (self.tr("Nominal FPS"), f"{info.fps_nominal:.3f}"),
            (self.tr("Total frames"), str(info.total_frames)),
            (self.tr("Total duration (s)"), f"{info.duration_sec:.3f}"),
            (self.tr("Timestamps"), self.tr("Yes") if info.timestamps_available else self.tr("No")),
            (self.tr("Codec"), info.codec_name or "—"),
            (self.tr("Pixel format"), info.pix_fmt or "—"),
        ]

        # Used interval
        if info.kept_frames is not None:
            rows.extend([
                (self.tr("── Used interval ──"), ""),
                (self.tr("Used start (s)"),
                 "—" if info.used_start_sec is None else f"{info.used_start_sec:.3f}"),
                (self.tr("Used end (s)"),
                 "—" if info.used_end_sec is None else f"{info.used_end_sec:.3f}"),
                (self.tr("Kept frames"), str(info.kept_frames)),
                (self.tr("Kept duration (s)"),
                 "—" if info.kept_duration_sec is None else f"{info.kept_duration_sec:.3f}"),
                (self.tr("Trimmed at start"), str(info.trimmed_start_frames)),
                (self.tr("Trimmed at end"), str(info.trimmed_end_frames)),
            ])

        self.panel_video.set_warning(None)
        self.panel_video.set_rows(rows)

    def set_aligned_info(self, info: AlignedInfo | None) -> None:
        if info is None:
            self.panel_aligned.set_rows([
                (self.tr("Status"), self.tr("Not yet aligned")),
            ])
            self.panel_aligned.set_warning(None)
            return

        # --- Warnings ---
        if info.overlap_status == "none":
            self.panel_aligned.set_warning(
                info.error_message or self.tr("No temporal overlap!")
            )
        elif info.overlap_status == "partial":
            parts: list[str] = []
            if info.video_trimmed_at_start:
                parts.append(
                    self.tr("Video trimmed at start ({n} frames)").format(
                        n=info.trimmed_start_frames
                    )
                )
            if info.video_trimmed_at_end:
                parts.append(
                    self.tr("Video trimmed at end ({n} frames)").format(
                        n=info.trimmed_end_frames
                    )
                )
            if info.data_discarded_before_sec > 0:
                parts.append(
                    self.tr("Data discarded before overlap ({s:.1f}s)").format(
                        s=info.data_discarded_before_sec
                    )
                )
            if info.data_discarded_after_sec > 0:
                parts.append(
                    self.tr("Data discarded after overlap ({s:.1f}s)").format(
                        s=info.data_discarded_after_sec
                    )
                )
            self.panel_aligned.set_warning("\n".join(parts) if parts else None)
        else:
            self.panel_aligned.set_warning(None)

        fps_str = "—" if info.real_fps is None else f"{info.real_fps:.3f}"

        self.panel_aligned.set_rows([
            (self.tr("Overlap status"), info.overlap_status),
            (self.tr("Aligned points"), str(info.points)),
            (self.tr("Time range (s)"), f"{info.t_min_sec:.3f} — {info.t_max_sec:.3f}"),
            (self.tr("Duration (s)"), f"{info.duration_sec:.3f}"),
            (self.tr("Interpolation"), info.interpolation),
            (self.tr("Normalized timestamps"),
             self.tr("Yes") if info.normalized_timestamps else self.tr("No")),
            (self.tr("Temperature"),
             self.tr("Yes") if info.temp_available else self.tr("No")),
            (self.tr("Speed"),
             self.tr("Yes") if info.speed_available else self.tr("No")),
            (self.tr("Real FPS"), fps_str),
            (self.tr("Temp smoothing window"), str(info.temp_smoothing_window)),
            (self.tr("Speed smoothing window"), str(info.speed_smoothing_window)),
        ])
