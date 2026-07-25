call uic.cmd
if not exist pyinstaller mkdir pyinstaller
cd pyinstaller
uv run python ../devtools/splash_gen.py
uv run pyinstaller ../vta_video_overlay/__main__.py -n vta-video-overlay --noconfirm -i ../assets/icon.png --splash splash.png --exclude-module matplotlib
xcopy ..\LICENSE .\dist\vta-video-overlay\
xcopy ..\LICENSE_RU .\dist\vta-video-overlay\
