[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.15213766.svg)](https://doi.org/10.5281/zenodo.15213766)
# VTA Video Overlay Tool
![Application Logo](assets/icon.png)

Desktop application for overlaying VPTAnalyzer (VTA) sensor data onto video recordings. Supports visualization of EMF, temperature, and metadata with customizable overlay elements.

## Features

- **Data Overlay**:
  - Displays time, EMF (mV), temperature (°C), operator, and sample information
  - Temperature calibration through polynomial coefficients
  - Configurable main and additional text sizes

- **File Processing**:
  - Import `.tda` sensor data files
  - Process ASF/MP4 video files
  - Export to MP4 with H.264/HEVC/MPEG-4 codecs
  - Batch conversion of `.tda` files to formatted Excel reports with charts

- **Tools**:
  - Interactive crop selection with real-time preview
  - Multi-language support (English/Russian) with automatic system locale detection
  - Operation logging and error handling

## Requirements

- Python 3.11+ (recommended 3.12)
- [FFmpeg & FFprobe](https://ffmpeg.org/download.html) in system PATH
- [uv](https://docs.astral.sh/uv/) for dependency management

## Installation

```bash
git clone https://gitflic.ru/project/i-o-yurev/vta-video-overlay.git
cd vta-video-overlay
uv sync
```

This creates a virtual environment at `.venv` with all dependencies installed.

## Build from Source

**Windows:**
```cmd
build.cmd
```

**Linux:**
```bash
bash build.sh
```

Build artifacts will be placed in `pyinstaller/dist`.

## Usage

### Initial Setup
Generate UI files and translations:
```cmd
uic.cmd  # Windows
bash uic.sh  # Linux
```

### Running the Application
```bash
uv run python -m vta_video_overlay
```

### Workflow
1. **File Selection**:
   - Select `.tda` sensor data file
   - Choose input video file (ASF/MP4)

2. **Configuration**:
   - Enter operator/sample information
   - Adjust temperature calibration coefficients
   - Enable/disable Excel export

3. **Video Cropping** (optional):
   - Use crop tool to select region
   - Adjust via numeric inputs or interactive GUI

4. **Processing**:
   - Set output path
   - Monitor progress in status bar
   - Preview processed video

![Application Interface](screenshot.png)

## Configuration

Create/edit `config.ini` in the application data folder:
```ini
[Overlay]
additional_text = "Custom Text"
additional_text_enabled = True
logo_enabled = True
main_text_size = 60
additional_text_size = 40
language = en
```

### Configuration Paths
- **Windows**: `%APPDATA%\vta_video_overlay`
- **Linux**: `~/.local/share/vta_video_overlay`

Place `logo.png` in the executable folder for custom branding.

## License

MIT License. See [LICENSE](LICENSE) for details.

---

[Changelog](CHANGELOG.md) | [Report Issue](https://gitflic.ru/project/i-o-yurev/vta-video-overlay/issue) | [Русская версия](README_RU.md)
```
