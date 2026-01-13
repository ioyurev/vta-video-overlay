import cv2
import numpy as np
from PySide6 import QtCore

from vta_video_overlay.config import config
from vta_video_overlay.crop_selection_widgets import RectangleGeometry
from vta_video_overlay.enums import Alignment
from vta_video_overlay.opencv_frame import CVFrame


def make_frame(
    img: cv2.typing.MatLike,
    crop_rect: RectangleGeometry | None,
    time: float,
    emf: float,
    temp: float | None,
    temp_speed: float | None,
    graph_img: np.ndarray | None,
    operator_name: str,
    sample_name: str,
    add_text: str | None,
):
    """Создает кадр с наложением данных и графика."""
    cvframe = CVFrame(image=img)
    if crop_rect is not None:
        cvframe.crop_by_rect(crop_rect)
    
    # Логика наложения графика (OpenCV Overlay)
    if graph_img is not None:
        # Размеры графика
        gh, gw = graph_img.shape[:2]
        # Размеры кадра
        fh, fw = cvframe.image.shape[:2]
        
        # Координаты (из конфига)
        x_offset = fw - gw 
        y_offset = config.text.margin_y
        
        # Проверяем, влезает ли график
        if x_offset > 0 and y_offset + gh < fh and x_offset + gw <= fw:
            # Вырезаем область интереса (ROI) из основного кадра
            roi = cvframe.image[y_offset:y_offset+gh, x_offset:x_offset+gw]
            
            # Разделяем каналы графика (BGR и Alpha)
            overlay_bgr = graph_img[:, :, :3]
            overlay_alpha = graph_img[:, :, 3] / 255.0
            
            # Альфа-блендинг: (Overlay * Alpha) + (ROI * (1 - Alpha))
            blended = (overlay_bgr * overlay_alpha[..., None] + 
                       roi * (1.0 - overlay_alpha[..., None]))
            
            # Записываем обратно в кадр
            cvframe.image[y_offset:y_offset+gh, x_offset:x_offset+gw] = blended.astype(np.uint8)
            
    if config.logo_enabled:
        cvframe.put_img(
            overlay_img=config.logo_img,
            x=cvframe.image.shape[1],
            y=cvframe.image.shape[0],
            align=Alignment.BOTTOM_RIGHT,
        )
    
    pilframe = cvframe.to_pilframe()
    
    # Отрисовка времени
    bbox = pilframe.put_text(
        text=QtCore.QCoreApplication.tr("t(s): {time:.1f}").format(time=time),  # type: ignore
        xy=(config.text.margin_x, config.text.margin_y),
        align=Alignment.TOP_LEFT,
    )
    
    # Отрисовка EMF ниже времени
    bbox = pilframe.put_text(
        text=QtCore.QCoreApplication.tr("E(mV): {emf:.2f}").format(emf=emf),  # type: ignore
        xy=(config.text.margin_x, config.text.line_spacing + bbox[3]),
        align=Alignment.TOP_LEFT,
    )
    
    # Отрисовка Температуры и Скорости
    if temp is not None:
        # Температура
        bbox = pilframe.put_text(
            text=f"T(°C): {temp:.0f}",
            xy=(config.text.margin_x, config.text.line_spacing + bbox[3]),
            align=Alignment.TOP_LEFT,
        )
        
        # Скорость отображается ВСЕГДА (4-я строка)
        if temp_speed is not None:
            bbox = pilframe.put_text(
                text=QtCore.QCoreApplication.tr("dT/dt(°C/s): {speed:.2f}").format(speed=temp_speed), # type: ignore
                xy=(config.text.margin_x, config.text.line_spacing + bbox[3]),
                align=Alignment.TOP_LEFT,
            )
    
    if add_text is not None:
        bbox = pilframe.put_text(
            text=add_text,
            xy=(config.text.margin_x, cvframe.size.height - config.text.margin_y),
            align=Alignment.BOTTOM_LEFT,
            small=True,
        )
        xy = (config.text.margin_x, bbox[1] - config.text.line_spacing)
    else:
        xy = (config.text.margin_x, cvframe.size.height - config.text.margin_y)
    
    bbox = pilframe.put_text(
        text=operator_name, xy=xy, align=Alignment.BOTTOM_LEFT, small=True
    )
    bbox = pilframe.put_text(
        text=sample_name,
        xy=(config.text.margin_x, bbox[1] - config.text.line_spacing),
        align=Alignment.BOTTOM_LEFT,
    )
    cvframe = CVFrame.from_pilframe(frame=pilframe)
    return cvframe
