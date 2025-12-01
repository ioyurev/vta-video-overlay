import sys
import traceback
from types import TracebackType
from typing import Type

from loguru import logger as log
from PySide6.QtCore import Qt

# from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication, QMessageBox


def set_excepthook():
    sys.excepthook = excepthook


def excepthook(
    exc_type: Type[BaseException],  # Тип исключения (например, ValueError)
    exc_value: BaseException,  # Экземпляр исключения
    exc_traceback: TracebackType | None,  # Трассировка (может быть None)
) -> None:
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))

    # Всегда выводим в консоль
    print("Необработанное исключение:\n", error_msg)

    # Проверяем, существует ли QApplication
    app = QApplication.instance()
    if app is not None:
        # Создаем окно с ошибкой
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle("Critical Error")
        msg_box.setText(f"<b>{exc_type.__name__}:</b> {exc_value}")
        msg_box.setDetailedText(error_msg)
        msg_box.setWindowModality(Qt.WindowModality.ApplicationModal)

        # Увеличиваем минимальный размер для удобства
        msg_box.setMinimumSize(400, 600)

        # Запускаем диалог
        msg_box.exec()
    else:
        log.error("Ошибка до инициализации QApplication. Консольный вывод:", error_msg)
