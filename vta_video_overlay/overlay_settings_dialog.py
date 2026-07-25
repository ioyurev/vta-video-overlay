from PySide6 import QtWidgets

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

        config.update()
        self.accept()
