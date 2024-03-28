bash uic.sh
if [ ! -d "pyinstaller" ]; then
    mkdir -p pyinstaller
fi
cd pyinstaller
pyinstaller ../vta_video_overlay/__main__.py -n vta-video-overlay --noconfirm -i ../assets/icon.png
cp ../LICENSE dist/vta-video-overlay/
cp ../LICENSE_RU dist/vta-video-overlay/
