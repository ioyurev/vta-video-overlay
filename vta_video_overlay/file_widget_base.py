"""
Base widget for displaying file information
"""

from pathlib import Path

import numpy as np
from PySide6 import QtCore, QtWidgets


class FileDataWidgetBase(QtWidgets.QWidget):
    def __init__(
        self,
        sample: str,
        operator: str,
        path: Path,
        time: np.ndarray,
        emf: np.ndarray,
        temp: np.ndarray | None,
    ):
        super().__init__()
        self.sample = sample
        self.operator = operator
        self.path = path
        self.time = time
        self.emf = emf
        self.temp = temp

        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)

        # Basic info
        basic_group = QtWidgets.QGroupBox("Basic Information")
        basic_layout = QtWidgets.QFormLayout()

        self.sample_label = QtWidgets.QLabel(self.sample)
        self.sample_label.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse
        )
        basic_layout.addRow("Sample:", self.sample_label)

        self.operator_label = QtWidgets.QLabel(self.operator)
        self.operator_label.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse
        )
        basic_layout.addRow("Operator:", self.operator_label)

        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

        # Statistics
        stats_group = QtWidgets.QGroupBox("Statistics")
        stats_layout = QtWidgets.QFormLayout()

        time_length = len(self.time) if self.time is not None else 0
        time_duration = (
            f"{max(self.time):.2f}"
            if self.time is not None and len(self.time) > 0
            else "0.00"
        )

        stats_layout.addRow("Points:", QtWidgets.QLabel(str(time_length)))
        stats_layout.addRow("Duration (s):", QtWidgets.QLabel(time_duration))
        stats_layout.addRow(
            "Temperature data:",
            QtWidgets.QLabel("Available" if self.temp is not None else "N/A"),
        )

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # Add specific content area - to be overridden by subclasses
        self.add_specific_content(layout)

        layout.addStretch()

    def add_specific_content(self, layout: QtWidgets.QVBoxLayout):
        """Override this method in subclasses to add specific content"""
        pass
