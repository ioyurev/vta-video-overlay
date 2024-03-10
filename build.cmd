call uic.cmd
cd pyinstaller
pyinstaller ../vta_video_overlay/__main__.py -n vta-video-overlay --noconfirm
xcopy ..\LICENSE .\dist\vta-video-overlay\
