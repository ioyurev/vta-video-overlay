from PySide6 import QtCore, QtWidgets

from vta_video_overlay.config import config


class OverlaySettingsDialog(QtWidgets.QDialog):
    """Диалоговое окно настройки видимости элементов наложения (оверлея)."""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setWindowTitle(self.tr("Overlay Settings"))
        self.resize(360, 420)

        main_layout = QtWidgets.QVBoxLayout(self)

        # Группа: Текстовые элементы наложения
        gb_text = QtWidgets.QGroupBox(self.tr("Text Overlay Elements"))
        layout_text = QtWidgets.QVBoxLayout(gb_text)

        self.cb_time = QtWidgets.QCheckBox(self.tr("Time t(s)"))
        self.cb_time.setChecked(config.text.show_time)
        layout_text.addWidget(self.cb_time)

        self.cb_emf = QtWidgets.QCheckBox(self.tr("EMF E(mV)"))
        self.cb_emf.setChecked(config.text.show_emf)
        layout_text.addWidget(self.cb_emf)

        self.cb_temp = QtWidgets.QCheckBox(self.tr("Temperature T(°C)"))
        self.cb_temp.setChecked(config.text.show_temp)
        layout_text.addWidget(self.cb_temp)

        self.cb_speed = QtWidgets.QCheckBox(self.tr("Heating Rate dT/dt(°C/s)"))
        self.cb_speed.setChecked(config.text.show_speed)
        layout_text.addWidget(self.cb_speed)

        self.cb_operator = QtWidgets.QCheckBox(self.tr("Operator Name"))
        self.cb_operator.setChecked(config.text.show_operator)
        layout_text.addWidget(self.cb_operator)

        self.cb_sample = QtWidgets.QCheckBox(self.tr("Sample Name"))
        self.cb_sample.setChecked(config.text.show_sample)
        layout_text.addWidget(self.cb_sample)

        # Дополнительный текст
        self.cb_add_text = QtWidgets.QCheckBox(self.tr("Additional Text"))
        self.cb_add_text.setChecked(config.additional_text_enabled)
        layout_text.addWidget(self.cb_add_text)

        self.edit_add_text = QtWidgets.QLineEdit()
        self.edit_add_text.setText(config.additional_text.strip())
        self.edit_add_text.setEnabled(config.additional_text_enabled)
        self.cb_add_text.toggled.connect(self.edit_add_text.setEnabled)
        layout_text.addWidget(self.edit_add_text)

        main_layout.addWidget(gb_text)

        # Группа: Графика и логотип
        gb_media = QtWidgets.QGroupBox(self.tr("Graphics & Logo"))
        layout_media = QtWidgets.QVBoxLayout(gb_media)

        self.cb_logo = QtWidgets.QCheckBox(self.tr("Show Logo"))
        self.cb_logo.setChecked(config.logo_enabled)
        layout_media.addWidget(self.cb_logo)

        self.cb_graph = QtWidgets.QCheckBox(self.tr("Show Speed Graph"))
        self.cb_graph.setChecked(config.graph.enabled)
        layout_media.addWidget(self.cb_graph)

        main_layout.addWidget(gb_media)

        # Группа: Настройки кодирования видео
        gb_encoder = QtWidgets.QGroupBox(self.tr("Video Encoding Settings"))
        layout_encoder = QtWidgets.QVBoxLayout(gb_encoder)

        # 1. Выбор кодека (Динамически по поддерживаемым видеокартой/процессором)
        from vta_video_overlay.codec_checker import get_available_codecs

        layout_codec = QtWidgets.QHBoxLayout()
        layout_codec.addWidget(QtWidgets.QLabel(self.tr("Codec:")))
        self.combo_codec = QtWidgets.QComboBox()
        available_codecs = get_available_codecs()
        for label, codec_id in available_codecs:
            self.combo_codec.addItem(label, codec_id)

        # Устанавливаем текущий кодек
        idx = self.combo_codec.findData(config.video_encoding.codec)
        if idx >= 0:
            self.combo_codec.setCurrentIndex(idx)
        layout_codec.addWidget(self.combo_codec)
        layout_encoder.addLayout(layout_codec)

        # 2. Ползунок качества CRF (0 - Lossless, 15-17 - Visually Lossless, 23 - Recommended)
        def format_crf_label(val: int) -> str:
            if val == 0:
                return f"CRF: {val} (Lossless / Без потерь)"
            elif 1 <= val <= 17:
                return f"CRF: {val} (Visually Lossless / Неотличимое)"
            elif 18 <= val <= 23:
                return f"CRF: {val} (High Quality / Рекомендуемый)"
            else:
                return f"CRF: {val} (Maximum Compression)"

        self.lbl_crf = QtWidgets.QLabel(format_crf_label(config.video_encoding.crf))
        layout_encoder.addWidget(self.lbl_crf)

        self.slider_crf = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.slider_crf.setRange(0, 28)
        self.slider_crf.setValue(config.video_encoding.crf)
        self.slider_crf.valueChanged.connect(
            lambda val: self.lbl_crf.setText(format_crf_label(val))
        )
        layout_encoder.addWidget(self.slider_crf)

        # 3. Пресет скорости
        layout_preset = QtWidgets.QHBoxLayout()
        layout_preset.addWidget(QtWidgets.QLabel(self.tr("Preset:")))
        self.combo_preset = QtWidgets.QComboBox()
        self.combo_preset.addItem("Fast", "fast")
        self.combo_preset.addItem("Medium", "medium")
        self.combo_preset.addItem("Slow", "slow")

        idx_preset = self.combo_preset.findData(config.video_encoding.preset)
        if idx_preset >= 0:
            self.combo_preset.setCurrentIndex(idx_preset)
        layout_preset.addWidget(self.combo_preset)
        layout_encoder.addLayout(layout_preset)

        # 4. Настройка числа потоков CPU
        import os
        logical_count = os.cpu_count() or 4

        layout_threads = QtWidgets.QVBoxLayout()
        self.cb_all_threads = QtWidgets.QCheckBox(
            self.tr(f"Использовать все логические ядра ({logical_count})")
        )

        sub_layout_spin = QtWidgets.QHBoxLayout()
        sub_layout_spin.addWidget(QtWidgets.QLabel(self.tr("Указать число потоков:")))
        self.spin_threads = QtWidgets.QSpinBox()
        self.spin_threads.setRange(1, 64)
        self.spin_threads.setValue(config.video_encoding.render_threads)
        sub_layout_spin.addWidget(self.spin_threads)

        is_all = config.video_encoding.render_threads >= logical_count
        self.cb_all_threads.setChecked(is_all)
        self.spin_threads.setEnabled(not is_all)

        def on_cb_all_toggled(checked: bool):
            self.spin_threads.setEnabled(not checked)
            if checked:
                self.spin_threads.setValue(logical_count)

        self.cb_all_threads.toggled.connect(on_cb_all_toggled)

        layout_threads.addWidget(self.cb_all_threads)
        layout_threads.addLayout(sub_layout_spin)
        layout_encoder.addLayout(layout_threads)

        main_layout.addWidget(gb_encoder)

        # Диалоговые кнопки (OK / Cancel)
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept_settings)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

    def accept_settings(self):
        """Сохраняет измененные настройки в config и записывает их на диск."""
        config.text.show_time = self.cb_time.isChecked()
        config.text.show_emf = self.cb_emf.isChecked()
        config.text.show_temp = self.cb_temp.isChecked()
        config.text.show_speed = self.cb_speed.isChecked()
        config.text.show_operator = self.cb_operator.isChecked()
        config.text.show_sample = self.cb_sample.isChecked()

        config.additional_text_enabled = self.cb_add_text.isChecked()
        config.additional_text = self.edit_add_text.text()

        config.logo_enabled = self.cb_logo.isChecked()
        config.graph.enabled = self.cb_graph.isChecked()

        # Видео кодек
        config.video_encoding.codec = self.combo_codec.currentData()
        config.video_encoding.crf = self.slider_crf.value()
        config.video_encoding.preset = self.combo_preset.currentData()

        import os
        logical_count = os.cpu_count() or 4
        if self.cb_all_threads.isChecked():
            config.video_encoding.render_threads = logical_count
        else:
            config.video_encoding.render_threads = self.spin_threads.value()

        config.update()
        self.accept()
