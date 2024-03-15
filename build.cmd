call uic.cmd
if not exist pyinstaller mkdir pyinstaller
cd pyinstaller
pyinstaller ../vta_video_overlay/__main__.py -n vta-video-overlay --noconfirm -i ../assets/icon.png
xcopy ..\LICENSE .\dist\vta-video-overlay\
