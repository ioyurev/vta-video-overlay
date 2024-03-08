pyside6-uic.exe ui\src\MainWindow.ui > ui\MainWindow.py

autoflake -i --remove-all-unused-imports ui\MainWindow.py
