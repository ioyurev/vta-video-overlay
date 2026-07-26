from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd
from loguru import logger as log

from vta_video_overlay.tda_headers import Headers

if TYPE_CHECKING:
    from vta_video_overlay.data_file import Data


def export_data_to_excel(data: "Data", path: Path) -> None:
    log.info("Saving .xlsx: {path}".format(path=path))
    df = pd.DataFrame()
    df[Headers.TIME] = data.time.round(3)
    df[Headers.EMF] = data.emf.round(3)
    if data.temp is not None:
        df[Headers.TEMP] = data.temp.round()
    writer = pd.ExcelWriter(path, engine="xlsxwriter")
    sheet_name = "Sheet1"
    df.to_excel(excel_writer=writer, index=False, sheet_name=sheet_name)
    workbook = writer.book
    worksheet = writer.sheets[sheet_name]
    chart = workbook.add_chart({"type": "scatter", "subtype": "straight"})  # type: ignore
    if data.temp is not None:
        yaxis = Headers.TEMP
        col_idx = 2
    else:
        yaxis = Headers.EMF
        col_idx = 1

    max_row = len(df)
    series_data = {
        "categories": [sheet_name, 1, 0, max_row, 0],
        "values": [sheet_name, 1, col_idx, max_row, col_idx],
    }
    chart.add_series(series_data)
    chart.set_legend({"position": "none"})
    chart.set_x_axis({"name": Headers.TIME})
    chart.set_y_axis({"name": yaxis})
    worksheet.insert_chart("E2", chart)
    workbook.close()
