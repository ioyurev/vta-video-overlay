call uic.cmd
if not exist pyinstaller mkdir pyinstaller
cd pyinstaller
python ../splash_gen.py
pyinstaller ../vta_video_overlay/__main__.py -n vta-video-overlay --noconfirm -i ../assets/icon.png --splash splash.png
xcopy ..\LICENSE .\dist\vta-video-overlay\
xcopy ..\LICENSE_RU .\dist\vta-video-overlay\
