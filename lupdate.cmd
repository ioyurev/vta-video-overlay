pyside6-lupdate.exe ^
assets\MainWindow.ui ^
assets\CropSelectionWindow.ui ^
vta_video_overlay\__main__.py ^
vta_video_overlay\config.py ^
vta_video_overlay\about_window.py ^
vta_video_overlay\ffmpeg_utils.py ^
vta_video_overlay\main_window.py ^
vta_video_overlay\opencv_processor.py ^
vta_video_overlay\tda_file.py ^
vta_video_overlay\video_data.py ^
vta_video_overlay\worker.py ^
-ts translation_ru.ts

python devtools/linguist_fixer.py
