from pathlib import Path
import pandas as pd
import numpy as np
from loguru import logger as log
from PySide6 import QtCore

from vta_video_overlay.aligned_data import calculate_speed
from vta_video_overlay.tda_headers import Headers


class Data(QtCore.QObject):
    operator: str
    sample: str
    path: Path
    time: np.ndarray
    emf: np.ndarray
    temp: np.ndarray | None

    @property
    def speed(self) -> np.ndarray | None:
        """
        Ленивый расчёт скорости по исходным данным.
        Используется ТОЛЬКО для диалога предпросмотра данных.
        Для видео оверлея используется VideoData.
        """
        if self.temp is None:
            return None
        
        # Используем общую логику расчета скорости
        speed = calculate_speed(self.time, self.temp)
        
        log.info(f"Raw data speed calculated: {len(speed)} points")
        return speed

    def to_excel(self, path: Path):
        log.info(self.tr("Saving .xlsx: {path}").format(path=path))
        df = pd.DataFrame()
        df[Headers.TIME] = self.time.round(3)
        df[Headers.EMF] = self.emf.round(3)
        if self.temp is not None:
            df[Headers.TEMP] = self.temp.round()
        writer = pd.ExcelWriter(path, engine="xlsxwriter")
        sheet_name = "Sheet1"
        df.to_excel(excel_writer=writer, index=False, sheet_name=sheet_name)
        workbook = writer.book
        worksheet = writer.sheets[sheet_name]
        chart = workbook.add_chart({"type": "scatter", "subtype": "straight"})  # type: ignore
        if self.temp is not None:
            column = "C"
            yaxis = Headers.TEMP
        else:
            column = "B"
            yaxis = Headers.EMF
        series_data = {
            "categories": f"={sheet_name}!$A:$A",
            "values": f"={sheet_name}!${column}:${column}",
        }
        chart.add_series(series_data)
        chart.set_legend({"position": "none"})
        chart.set_x_axis({"name": Headers.TIME})
        chart.set_y_axis({"name": yaxis})
        worksheet.insert_chart("E2", chart)
        workbook.close()
