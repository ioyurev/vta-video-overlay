<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="ru_RU">
<context>
    <name>AboutWindow</name>
    <message>
        <location filename="vta_video_overlay/about_window.py" line="11"/>
        <source>About</source>
        <translation>О программе</translation>
    </message>
    <message>
        <location filename="vta_video_overlay/about_window.py" line="23"/>
        <source>Program for overlaying VTA data on video.</source>
        <oldsource>Program for video overlay of VTA data.</oldsource>
        <translation>Программа для наложения данных ВТА на видео.</translation>
    </message>
    <message>
        <location filename="vta_video_overlay/about_window.py" line="27"/>
        <source>Ilya O. Yurev, &lt;a href=&quot;mailto:{email}&quot;&gt;{email}&lt;/a&gt;</source>
        <translation>Илья Олегович Юрьев, &lt;a href=&quot;mailto:{email}&quot;&gt;{email}&lt;/a&gt;</translation>
    </message>
    <message>
        <location filename="vta_video_overlay/about_window.py" line="37"/>
        <source>Version: {v}</source>
        <translation>Версия: {v}</translation>
    </message>
</context>
<context>
    <name>App</name>
    <message>
        <location filename="vta_video_overlay/__main__.py" line="35"/>
        <source>Error</source>
        <translation>Ошибка</translation>
    </message>
    <message>
        <location filename="vta_video_overlay/__main__.py" line="36"/>
        <source>{bin} not found.</source>
        <translation>{bin} не найден.</translation>
    </message>
</context>
<context>
    <name>CVProcessor</name>
    <message>
        <location filename="vta_video_overlay/opencv_processor.py" line="40"/>
        <source>Operator: {operator}
</source>
        <translation>Оператор: {operator}
</translation>
    </message>
    <message>
        <location filename="vta_video_overlay/opencv_processor.py" line="43"/>
        <source>Sample: {sample}
</source>
        <translation>Образец: {sample}
</translation>
    </message>
    <message>
        <location filename="vta_video_overlay/opencv_processor.py" line="44"/>
        <source>Time (s): {time:.3f}
</source>
        <oldsource>Time (s): {{time.3f}}
</oldsource>
        <translation>Время (с): {time:.3f}
</translation>
    </message>
    <message>
        <location filename="vta_video_overlay/opencv_processor.py" line="45"/>
        <source>EMF (mV): {emf:.3f}</source>
        <oldsource>EMF (mV): {{emf:.3f}}</oldsource>
        <translation>ЭДС (мВ): {emf:.3f}</translation>
    </message>
    <message>
        <location filename="vta_video_overlay/opencv_processor.py" line="50"/>
        <source>
Temperature (C): {temp:.0f}</source>
        <oldsource>Temperature (C): {temp:.0f}</oldsource>
        <translation>
Температура (C): {temp:.0f}</translation>
    </message>
    <message>
        <location filename="vta_video_overlay/opencv_processor.py" line="56"/>
        <source>Time trim: {timestamp}, frame: {i}</source>
        <translation>Обрезка по времени: {timestamp}, кадру: {i}</translation>
    </message>
    <message>
        <location filename="vta_video_overlay/opencv_processor.py" line="102"/>
        <source>Video resolution: {size}</source>
        <translation>Разрешение видео: {size}</translation>
    </message>
    <message>
        <location filename="vta_video_overlay/opencv_processor.py" line="115"/>
        <source>OpenCV has finished</source>
        <translation>OpenCV завершил работу</translation>
    </message>
</context>
<context>
    <name>Data</name>
    <message>
        <location filename="vta_video_overlay/tda_file.py" line="69"/>
        <source>Saving .xlsx: {path}</source>
        <translation>Сохранение .xlsx: {path}</translation>
    </message>
</context>
<context>
    <name>FFmpeg</name>
    <message>
        <location filename="vta_video_overlay/ffmpeg_utils.py" line="35"/>
        <source>Video stream not found.</source>
        <translation>Видео поток не найден.</translation>
    </message>
    <message>
        <location filename="vta_video_overlay/ffmpeg_utils.py" line="56"/>
        <source>Invalid path for the video file: &quot;{path}&quot;</source>
        <translation>Неверный путь к видеофайлу: &quot;{path}&quot;</translation>
    </message>
    <message>
        <source>The file {path} is not a video file or the file does not exist.</source>
        <translation type="vanished">Файл {path} не является видеофайлом или файл не существует.</translation>
    </message>
    <message>
        <source>The index {i} is not in the file {path}.</source>
        <translation type="vanished">Индекс {i} отсутствует в файле {path}.</translation>
    </message>
    <message>
        <source>The index {i} is not a video stream. It is an {type} stream.</source>
        <translation type="vanished">Индекс {i} не является видеопотоком. Это поток {type}.</translation>
    </message>
    <message>
        <location filename="vta_video_overlay/ffmpeg_utils.py" line="95"/>
        <source>Converting file: {path}</source>
        <translation>Преобразование файла: {path}</translation>
    </message>
    <message>
        <location filename="vta_video_overlay/ffmpeg_utils.py" line="96"/>
        <source>Saving to: {path}</source>
        <translation>Сохранение в: {path}</translation>
    </message>
    <message>
        <location filename="vta_video_overlay/ffmpeg_utils.py" line="101"/>
        <source>ffmpeg conversion finished.</source>
        <translation>Преобразование ffmpeg завершено.</translation>
    </message>
</context>
<context>
    <name>MainWindow</name>
    <message>
        <source>Version: {v}</source>
        <translation>Версия: {v}</translation>
    </message>
    <message>
        <source>About</source>
        <translation>О программе</translation>
    </message>
    <message>
        <source>VPTAnalizer file(*.tda)</source>
        <translation>Файл VPTAnalizer(*.tda)</translation>
    </message>
    <message>
        <source>Failed to read TDA file.</source>
        <translation>Не удалось прочитать файл TDA.</translation>
    </message>
    <message>
        <source>Video(*.asf *.mp4);;All files(*.*)</source>
        <translation>Видео(*.asf *.mp4);;Все файлы(*.*)</translation>
    </message>
    <message>
        <source>Failed to read video file.</source>
        <translation>Не удалось прочитать видео файл.</translation>
    </message>
    <message>
        <source>Video processing completed</source>
        <translation>Обработка видео завершена</translation>
    </message>
    <message>
        <source>Video processing failed.
Exception occurred. See log.</source>
        <translation>Не удалось обработать видео.
Произошло исключение. См. журнал.</translation>
    </message>
    <message>
        <source>Operator: {operator}</source>
        <translation>Оператор: {operator}</translation>
    </message>
    <message>
        <source>Sample: {sample}</source>
        <translation>Образец: {sample}</translation>
    </message>
    <message>
        <source>Temperature calibration enabled: {bool}</source>
        <translation>Калибровка температуры включена: {bool}</translation>
    </message>
    <message>
        <source>Polynomial coefficients: {coeff}</source>
        <translation>Коэффициенты полинома: {coeff}</translation>
    </message>
    <message>
        <source>Select video file</source>
        <translation>Выбрать видеофайл</translation>
    </message>
    <message>
        <source>Temperature calibration y = a3*x^3 + a2*x^2 + a1*x + a0</source>
        <translation>Температурная калибровка y = a3*x^3 + a2*x^2 + a1*x + a0</translation>
    </message>
    <message>
        <source>(Experimental) overlay dE/dt plot</source>
        <translation>(Экспериментальное) наложить график dE/dt</translation>
    </message>
    <message>
        <source>Operator:</source>
        <translation>Оператор:</translation>
    </message>
    <message>
        <source>Start video processing</source>
        <translation>Начать обработку видео</translation>
    </message>
    <message>
        <source>Select .tda file</source>
        <translation>Выбрать файл .tda</translation>
    </message>
    <message>
        <source>Trim from (sec):</source>
        <translation>Обрезать от (сек):</translation>
    </message>
    <message>
        <source>Convert .tda to .xlsx</source>
        <translation>Конвертировать .tda в .xlsx</translation>
    </message>
    <message>
        <source>Sample:</source>
        <translation>Образец:</translation>
    </message>
</context>
<context>
    <name>QtCore.QCoreApplication</name>
    <message>
        <location filename="vta_video_overlay/main_window.py" line="26"/>
        <source>Video(*.mp4)</source>
        <translation>Видео(*.mp4)</translation>
    </message>
    <message>
        <location filename="vta_video_overlay/main_window.py" line="29"/>
        <source>All files(*.*)</source>
        <translation>Все файлы(*.*)</translation>
    </message>
</context>
<context>
    <name>VideoData</name>
    <message>
        <location filename="vta_video_overlay/video_data.py" line="21"/>
        <source>Number of video frames: {len}</source>
        <translation>Количество видеокадров: {len}</translation>
    </message>
</context>
</TS>
