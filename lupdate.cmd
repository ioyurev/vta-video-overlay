pyside6-lupdate.exe ^
assets\MainWindow.ui ^
vta_video_overlay\__main__.py ^
vta_video_overlay\AboutWindow.py ^
vta_video_overlay\FFmpeg.py ^
vta_video_overlay\MainWindow.py ^
vta_video_overlay\OpenCV.py ^
vta_video_overlay\TdaFile.py ^
vta_video_overlay\VideoData.py ^
-ts translation_ru.ts

python devtools/linguist_fixer.py
