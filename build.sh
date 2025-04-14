bash uic.sh
mkdir -p pyinstaller
cd pyinstaller || exit
python ../devtools/splash_gen.py
pyinstaller ../vta_video_overlay/__main__.py -n vta-video-overlay --noconfirm -i ../assets/icon.png --splash splash.png --exclude-module matplotlib
cp ../LICENSE ./dist/vta-video-overlay/
cp ../LICENSE_RU ./dist/vta-video-overlay/
