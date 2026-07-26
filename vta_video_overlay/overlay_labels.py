from PySide6 import QtCore


def build_overlay_labels(operator: str, sample: str) -> tuple[str, str]:
    return (
        QtCore.QCoreApplication.translate("make_frame", "Operator: {name}").format(
            name=operator
        ),
        QtCore.QCoreApplication.translate("make_frame", "Sample: {name}").format(
            name=sample
        ),
    )
