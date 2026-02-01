"""
Configuration settings for SFO File Organizer.
"""

import os
import sys
import shutil
from pathlib import Path

def get_resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_data_dir() -> Path:
    """Get path to persistent data directory (APPDATA on Windows)."""
    if getattr(sys, 'frozen', False):
        # Running as bundled exe
        app_data = os.getenv('APPDATA')
        if app_data:
            path = Path(app_data) / "SFOFileOrganizer"
        else:
            path = Path(sys.executable).parent / "data"
    else:
        # Running in dev
        path = Path(__file__).parent
    
    # Ensure directory exists
    try:
        path.mkdir(parents=True, exist_ok=True)
    except Exception:
        # Fallback to current directory if all else fails
        path = Path(".")
        
    return path

# Data directory for persistent storage (History, Custom Rules)
# We use APPDATA to ensure data survives app updates/moves
APPDATA_PATH = os.environ.get("APPDATA", os.path.expanduser("~"))
DATA_DIR = Path(APPDATA_PATH) / "SFOFileOrganizer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Define paths for data files
HISTORY_FILE = DATA_DIR / "organizer_history.json"
CUSTOM_RULES_FILE = DATA_DIR / "custom_rules.json"

def initialize_data():
    """Copy default data files to the persistent DATA_DIR if they don't exist."""
    defaults = [CUSTOM_RULES_FILE.name] # Use .name to get "custom_rules.json"
    for filename in defaults:
        dest_path = DATA_DIR / filename
        if not dest_path.exists():
            source_path = get_resource_path(filename)
            if os.path.exists(source_path) and source_path != str(dest_path):
                try:
                    shutil.copy2(source_path, dest_path)
                except Exception:
                    pass

initialize_data()

# Default directories (in-place organization by default)
DEFAULT_SOURCE_DIR = str(Path.home() / "Downloads")
DEFAULT_DEST_DIR = DEFAULT_SOURCE_DIR  # Same as source for in-place organizing

# File categories and their extensions
FILE_CATEGORIES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico", ".tiff"],
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".xls", ".xlsx", ".ppt", ".pptx"],
    "Videos": [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm"],
    "Audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
    "Code": [".py", ".js", ".html", ".css", ".java", ".cpp", ".c", ".h", ".json", ".xml", ".php", ".ts", ".tsx", ".jsx"],
    "Executables": [".exe", ".msi", ".bat", ".sh", ".app", ".dmg"],
    "Fonts": [".ttf", ".otf", ".woff", ".woff2"],
}

# Logging settings
LOG_FILE = "organizer.log"
LOG_LEVEL = "INFO"

# Detailed categories for Smart Context mode (Sub-types for Documents)
DETAILED_CATEGORIES = {
    # Documents breakdown
    ".pdf": "PDFs",
    ".doc": "Word Documents", ".docx": "Word Documents",
    ".xls": "Spreadsheets", ".xlsx": "Spreadsheets", ".csv": "Spreadsheets",
    ".ppt": "Presentations", ".pptx": "Presentations",
    ".txt": "Text Files", ".md": "Text Files", ".rtf": "Text Files",
}
