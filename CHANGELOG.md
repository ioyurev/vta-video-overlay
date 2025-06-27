## 0.6.0 (2025-06-27)

### Feat

- add vtaz format support

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
- remove cli implementation
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

## 0.3.1 (2024-03-17)

### Fix

- **__main__.py**: fixed an error at startup of the compiled distribution package

## 0.3.0 (2024-03-17)

### Feat

- добавлен перевод
- **TdaFile.py**: реализовано добавление графика в файл Excel
- отображение предпросмотра видео в интерфейсе PySide6 вместо OpenCV
- **FFmpeg.py**: добавлена функция получения разрешения видео с помощью ffprobe
- добавлено окно о программе
- добавлена иконка программы
- запись в лог информации об измерении
- добавлена возможность обрезки видео от определенной временной отметки

### Fix

- **MainWindow**: исправлено исключение в случае выбора пустого пути
- **build.cmd**: исправлена невозможность сборки из-за отсутствия попдпапки для хранения файлов сборки
- **MainWindow**: исправлено отображение температуры, если выключена температурная калибровка

### Refactor

- **MainWindow**: указан тип сигнала для слота update_progressbar
- **OpenCV.py**: убран неиспользуемый код
- **MainWindow.py**: применен декоратор QtCore.Slot для соотвествующих методов
- **OpenCV.py**: переработаны алгоритмы подготовки и отрисовки оверлея

## 0.2.0 (2024-03-10)

### Feat

- добавлена запись журнала сообщений
- реализовано ковертирование файла .tda в .xlsx
- **Worker.py**: добавлена очистка временных файлов по завершении обработки видео
- **Worker.py**: добавлено окно об ошибке обработки видео
- **__main__.py**: добавлена проверка наличия необходимых бинарных файлов
- **OpenCV.py**: установлен встроенный кодек mp4v, убрана зависимость от библиотеки openh264
- **MainWindow**: интерфейс подключен к потоку обработки видео
- **Worker.py**: обработка видео в отдельном потоке от интерфейса

### Fix

- **OpenCV.py**: исправлена ошибка, возникающая при превышении счетчика кадров
- **MainWindow**: исправлена опечатка
- **Worker.py**: исправлено значение прогресс бара
- **VideoData.py**: исправление регистра имени файла
- **Overlay.py**: исправлена ошибка запуска обработки в opencv

### Refactor

- **poetry**: удалена неиспользуемая зависимость
- **VideoData.py**: заменена функция интерполяции на np.interp, убрана зависимость от scipy
- **MainWindow**: интерфейс перекомпонован по сетке
- **Data**: изменен тип хранения данных на ndarray
- **OpenCV.py**: сообщения о прерывании цикла изменены на русский язык
- **OpenCV.py**: параметры цвета вынесены в константы
- **FFmpeg.py**: убрана константа бинарного файла FFmpeg
- функции FFmpeg и OpenCV разнесены в отдельные модули
