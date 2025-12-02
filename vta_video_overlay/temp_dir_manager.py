"""
Singleton manager for temporary directory handling

Key Responsibilities:
- Create and manage a single temporary directory for the application
- Ensure thread-safe access to the temporary directory
- Handle cleanup when requested from main window
"""

import os
import shutil
import tempfile
import threading
from pathlib import Path

from loguru import logger as log


def clean(tempdir: Path):
    log.info("Cleaning {tempdir}".format(tempdir=tempdir))
    if os.path.exists(tempdir):
        shutil.rmtree(tempdir)


class TempDirManager:
    """Singleton class to manage temporary directory lifecycle"""

    _temp_dir = None
    _lock = threading.Lock()
    _initialized = False

    @classmethod
    def get_temp_dir(cls) -> Path:
        """Get or create the temporary directory"""
        if cls._temp_dir is None:
            with cls._lock:
                if cls._temp_dir is None:
                    cls._temp_dir = Path(tempfile.mkdtemp())
                    cls._initialized = True
        return cls._temp_dir

    @classmethod
    def cleanup(cls):
        """Clean up the temporary directory and reset state"""
        if cls._temp_dir is not None:
            with cls._lock:
                if cls._temp_dir is not None:
                    clean(cls._temp_dir)
                    cls._temp_dir = None
                    cls._initialized = False

    @classmethod
    def is_initialized(cls) -> bool:
        """Check if temporary directory has been created"""
        return cls._initialized
