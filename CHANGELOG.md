## 0.3.0 (2024-03-18)

### Feat

- added translation
- **TdaFile.py**: added graphics to an Excel file
- video preview in PySide6 interface instead of OpenCV
- **FFmpeg.py**: added function to obtain video resolution using ffprobe.
- added about window
- added icon
- added logging of measurement information
- added the option to trim video from a user-defined timestamp

### Fix

- **MainWindow**: fixed exception if empty path was selected
- **build.cmd**: fixed build failure due to missing subfolder to store build files
- **MainWindow**: fixed temperature display when temperature calibration is off

### Refactor

- **MainWindow**: specified signal type for update_progressbar slot
- **OpenCV.py**: removed unused code
- **MainWindow.py**: applied QtCore.Slot decorator to corresponding methods
- **OpenCV.py**: reworked overlay preparation and rendering algorithms

## 0.2.0 (2024-03-10)

### Feat

- added logging
- implemented conversion of .tda file to .xlsx
- **Worker.py**: added clearing of temporary files after video processing is finished
- **Worker.py**: added video processing error window
- **__main__.py**: added check if necessary binary files are available
- **OpenCV.py**: selected built-in mp4v codec, removed dependency on external library openh264
- **MainWindow**: interface connected to video processing thread
- **Worker.py**: video processing in a separate thread from the interface

### Fix

- **OpenCV.py**: fixed an error occurring when the frame counter is exceeded
- **MainWindow**: fixed a typo
- **Worker.py**: fixed progress bar value
- **VideoData.py**: filename case correction
- **Overlay.py**: fixed error of starting processing in opencv

### Refactor

- **poetry**: removed unused dependency
- **VideoData.py**:  replaced interpolation function with np.interp, removed scipy dependency
- **MainWindow**: the interface has been rearranged in a grid layout
- **Data**: changed data storage type to ndarray
- **OpenCV.py**: loop interrupt messages changed to Russian language
- **OpenCV.py**: color parameters moved to constants
- **FFmpeg.py**: removed FFmpeg binary file constant
- FFmpeg and OpenCV functions moved to separate modules
