import configparser
import locale
import os
import sys
from pathlib import Path
from typing import Any, Final

import cv2
import matplotlib as mpl
from loguru import logger as log
from matplotlib.axes import Axes
from pydantic import BaseModel, Field, PrivateAttr

# --- КОНСТАНТЫ ЦВЕТОВ И ШРИФТОВ ---
TEXT_COLOR: Final = (0, 255, 255)
BG_COLOR: Final = (63, 63, 63)
BG_ALPHA: Final = 0.8

TEXT_COLOR_MPL: Final = (TEXT_COLOR[2] / 255, TEXT_COLOR[1] / 255, TEXT_COLOR[0] / 255)
BG_COLOR_MPL: Final = (BG_COLOR[2] / 255, BG_COLOR[1] / 255, BG_COLOR[0] / 255)

FONT_FILENAME: Final = "DejaVuSans.ttf"


def get_graph_size(frame_width: int, frame_height: int) -> tuple[int, int]:
    """Рассчитывает размер графика относительно кадра."""
    size = max(200, 3 * min(frame_width, frame_height) // 8)
    return size, size


def get_appdata_path() -> Path:
    app_folder = "vta_video_overlay"
    if sys.platform.startswith("linux"):
        appdata_folder = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
    else:
        appdata_folder = os.getenv("APPDATA") or os.path.expanduser("~")
    path = Path(appdata_folder) / app_folder
    path.mkdir(parents=True, exist_ok=True)
    return path


def setup_logging(appdata_path: Path) -> None:
    log_file_path = appdata_path / "logs/{time}.log"
    log.add(log_file_path, rotation="1 week", retention="1 month")


def get_default_language() -> str:
    try:
        loc = locale.getlocale()[0]
        if loc is not None:
            return loc.split("_")[0]
        return "en"
    except Exception:
        return "en"


# --- ВЛОЖЕННЫЕ МОДЕЛИ КОНФИГУРАЦИИ ---

class GraphSettings(BaseModel):
    """Настройки визуализации графика."""
    enabled: bool = True
    time_window: float = 30.0
    line_width: float = 1.5
    marker_size: int = 5
    # margin_top удален, так как используется text.margin_y
    speed_smoothing_window: int = 30
    temp_smoothing_window: int = 15


class TextSettings(BaseModel):
    """Настройки текста и отступов."""
    main_size: int = 60
    additional_size: int = 40
    margin_x: int = 5
    margin_y: int = 5
    line_spacing: int = 10
    bg_padding: int = 5


class Config(BaseModel):
    """Главный класс конфигурации приложения."""
    
    # Основные настройки
    logo_enabled: bool = True
    additional_text_enabled: bool = False
    additional_text: str = " "
    language: str = Field(default_factory=get_default_language)
    
    # Группы настроек
    graph: GraphSettings = Field(default_factory=GraphSettings)
    text: TextSettings = Field(default_factory=TextSettings)

    # Приватный атрибут для логотипа
    _logo_img: Any = PrivateAttr(default=None)

    def model_post_init(self, __context: Any) -> None:
        self._load_resources()

    def _load_resources(self) -> None:
        if self.logo_enabled:
            try:
                logo_path = Path("logo.png") 
                if logo_path.exists():
                    self._logo_img = cv2.imread(str(logo_path))
                
                if self._logo_img is None:
                    self.logo_enabled = False
            except Exception as e:
                log.error(f"Failed to load logo file: {e}")
                self.logo_enabled = False

    @property
    def logo_img(self) -> Any:
        return self._logo_img

    # --- Методы сериализации ---
    
    def to_json_file(self, path: Path) -> None:
        """Сохраняет конфигурацию в JSON файл."""
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=4))

    @classmethod
    def from_json_file(cls, path: Path) -> "Config":
        """Загружает конфигурацию из JSON файла."""
        with open(path, "r", encoding="utf-8") as f:
            json_data = f.read()
        return cls.model_validate_json(json_data)

    # --- Методы миграции и загрузки ---

    @classmethod
    def _migrate_from_ini(cls, ini_path: Path) -> "Config":
        """Миграция старого конфига из INI формата."""
        log.info(f"Migrating legacy config from {ini_path}")
        parser = configparser.ConfigParser()
        parser.read(ini_path, encoding="utf-8")
        
        data: dict[str, Any] = {}
        graph_data: dict[str, Any] = {}
        text_data: dict[str, Any] = {}

        if "Overlay" in parser:
            overlay = parser["Overlay"]
            
            if "logo_enabled" in overlay:
                data["logo_enabled"] = overlay.getboolean("logo_enabled")
            if "additional_text_enabled" in overlay:
                data["additional_text_enabled"] = overlay.getboolean("additional_text_enabled")
            if "additional_text" in overlay:
                data["additional_text"] = overlay["additional_text"]
            if "language" in overlay:
                data["language"] = overlay["language"]
            
            if "main_text_size" in overlay:
                text_data["main_size"] = overlay.getint("main_text_size")
            if "additional_text_size" in overlay:
                text_data["additional_size"] = overlay.getint("additional_text_size")

        if graph_data:
            data["graph"] = GraphSettings(**graph_data)
        if text_data:
            data["text"] = TextSettings(**text_data)

        return cls(**data)

    @classmethod
    def from_file(cls, json_path: Path, ini_path: Path | None = None) -> "Config":
        """
        Загружает конфигурацию из файла.
        
        Приоритет:
        1. config.json
        2. config.ini (миграция)
        3. Дефолтные значения
        """
        # Попытка загрузить JSON
        if json_path.exists():
            try:
                cfg = cls.from_json_file(json_path)
                log.debug("Loaded config from JSON")
                return cfg
            except Exception as e:
                log.error(f"Error loading JSON config: {e}")

        # Попытка миграции с INI
        if ini_path is not None and ini_path.exists():
            try:
                cfg = cls._migrate_from_ini(ini_path)
                cfg.to_json_file(json_path)
                log.info("Migration successful. New config.json created.")
                try:
                    ini_path.unlink()
                    log.info("Legacy config.ini deleted.")
                except OSError as e:
                    log.warning(f"Could not delete legacy config.ini: {e}")
                return cfg
            except Exception as e:
                log.error(f"Migration failed: {e}")

        # Создание дефолтного конфига
        log.warning("Creating new default config.")
        cfg = cls()
        cfg.update()
        return cfg

    def update(self) -> None:
        """Сохраняет текущую конфигурацию в файл."""
        try:
            self.to_json_file(CONFIG_PATH)
            log.info("Config file updated")
        except Exception as e:
            log.exception(f"Failed to save config: {e}")


# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ MATPLOTLIB ---

def setup_mpl_fonts() -> None:
    """Настраивает шрифты Matplotlib (базовая настройка)."""
    mpl.rcParams['font.family'] = 'sans-serif'
    mpl.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'sans-serif']


def style_graph_axes(ax: Axes, label_fontsize: float) -> None:
    """Применяет стандартный стиль к осям графика."""
    ax.tick_params(colors=TEXT_COLOR_MPL, labelsize=label_fontsize, direction='in')
    for spine in ax.spines.values():
        spine.set_color(TEXT_COLOR_MPL)
        spine.set_linewidth(1)


def setup_mpl_style() -> tuple[float, float]:
    """Настраивает Matplotlib (полная настройка) и возвращает (title_pt, label_pt)."""
    dpi = 100
    title_pt = config.text.additional_size * 72 / dpi
    label_pt = title_pt * 0.6
    
    setup_mpl_fonts()
    mpl.rcParams['font.size'] = label_pt
    
    return title_pt, label_pt


# --- Инициализация ---
appdata_path = get_appdata_path()
setup_logging(appdata_path)

CONFIG_PATH = appdata_path / "config.json"
INI_PATH = appdata_path / "config.ini"

config = Config.from_file(json_path=CONFIG_PATH, ini_path=INI_PATH)