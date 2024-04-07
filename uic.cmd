if not exist vta_video_overlay\ui mkdir vta_video_overlay\ui
pyside6-uic.exe assets\MainWindow.ui > vta_video_overlay\ui\MainWindow.py
autoflake -i --remove-all-unused-imports vta_video_overlay\ui\MainWindow.py
pyside6-lrelease.exe .\translation_ru.ts -qm assets\translation_ru.qm
pyside6-rcc.exe assets\resources.qrc > vta_video_overlay\ui\resources_rc.py
