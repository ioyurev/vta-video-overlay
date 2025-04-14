## 0.5.0 (2025-04-14)

### Feat

- **main_window.py**: replace logs folder menu action with config folder and update translations
- **config.py**: move language detection to config, add configurable language option, use system locale as default
- add configurable text size options for overlay
- **translation**: updated
- **opencv_processor.py**: added frame processing with PIL

### Fix

- **Pipeline**: initialize crop_rect with None in Pipeline class
- **config.py**: add check for logo image loading failure to disable logo if not found
- **config.py**: fixed read config file error
- more exceptions handling
- **video_data.py**: fixed expception for not defined temperature list
- **opencv_processor.py**: fixed text rendering when processing video without calibration
- **worker.py**: disabled exceptions handling for developening purposes
- fixed ghost selection
- fixed QObject parent warning
- **opencv_processor.py**: fixed additional rendering while it disabled
- fixed import exception for pyinstaller build
- **data_collections.py**: fixed startup error for pyinstaller build

### Refactor

- switch from relative to absolute imports
- refine logging levels with additional debug messages
- **pipeline.py**: split execute method into private helper methods
- add final type hints
- dead code removed
- **config.py**: some configs moved to config module
- **CVProcessor**: move progress signal to cvprocessor class, connect signal in worker, adjust constructor and signal emission
- trim disabled by default
- refactored text rendering
- refactored RectangeGeometry usage
- changed interaction with config

## 0.4.0 (2024-04-20)

### Feat

- **opencv_processor.py**: added additional text rendering
- added config file
- **opencv_processor.py**: added bottom border to frame
- **worker.py**: addded log message for temporary directory cleaning
- **main_window.py**: added check for selected data file
- added video cropping
- added crop selection feature
- added button to open logs folder
- added skipping video preconverting if there are timestamps in the source video file
- added linux support
- **__main__.py**: added message window output in case of environment check error
- **main_window.py**: added exception catching when selecting tda and video files
- **opencv_processor.py**: added disabling the plotter when plotting is turned off
- **translation_ru.ts**: updated translation
- added dialog box in case of exception in video processing
- **__main__.py**: logs have been moved to the program folder in AppData
- added feature to overlay dE/dt plot

### Fix

- **uic.sh**: added ui pre-compilation for crop selection window
- **crop_selection_window.py**: fixed window initialization
- **opencv_processor.py**: fixed invalid import of plotter
- **main_window.py**: fixed an error when an empty path is selected for saving video
- **linguist_fixer.py**: fixed error in context search

### Refactor

- adjusted text scale
- added isort
- **worker.py**: file renamed by snake_case
- defined the minimum version of python as 3.11
- updated translation
- modules renamed by snake_case

## 0.3.1 (2024-03-18)

### Fix

- **__main__.py**: fixed an error at startup of the compiled distribution package

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
