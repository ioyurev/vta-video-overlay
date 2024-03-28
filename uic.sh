if [ ! -d "vta_video_overlay/ui" ]; then
    mkdir -p vta_video_overlay/ui
fi
pyside6-uic assets/MainWindow.ui > vta_video_overlay/ui/MainWindow.py
autoflake -i --remove-all-unused-imports "vta_video_overlay/ui/MainWindow.py"
pyside6-lrelease "translation_ru.ts" -qm "assets/translation_ru.qm"
pyside6-rcc "assets/resources.qrc" > "vta_video_overlay/ui/resources_rc.py"
