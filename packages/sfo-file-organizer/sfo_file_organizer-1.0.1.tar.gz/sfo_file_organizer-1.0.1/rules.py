"""
Rule-based file classification engine for SFO File Organizer.

Provides keyword-based classification that takes priority over extension-based logic.
Supports both built-in rules and user-defined custom rules from the UI.
"""

import json
from pathlib import Path
from typing import Optional
from app_config import FILE_CATEGORIES, DATA_DIR

# Path to custom rules file (managed by rules_ui.py)
CUSTOM_RULES_FILE = DATA_DIR / "custom_rules.json"


def load_custom_rules() -> dict:
    """Load user-defined custom rules from JSON file."""
    if CUSTOM_RULES_FILE.exists():
        try:
            with open(CUSTOM_RULES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("keyword_rules", {})
        except Exception:
            pass
    return {}

# Keyword rules: maps keywords (in filename) to categories
# These take priority over extension-based classification
KEYWORD_RULES: dict[str, str] = {
    # Document-related keywords
    "invoice": "Documents",
    "receipt": "Documents",
    "contract": "Documents",
    "report": "Documents",
    "resume": "Documents",
    "cv": "Documents",
    "letter": "Documents",
    "statement": "Documents",
    "certificate": "Documents",
    "license": "Documents",
    "agreement": "Documents",
    "proposal": "Documents",
    "quotation": "Documents",
    "memo": "Documents",
    "minutes": "Documents",
    "payslip": "Documents",
    "paystack": "Documents",
    "merchant": "Documents",
    "tax": "Documents",
    "form": "Documents",
    
    # Image-related keywords
    "screenshot": "Images",
    "photo": "Images",
    "wallpaper": "Images",
    "banner": "Images",
    "logo": "Images",
    "icon": "Images",
    "image": "Images",
    "img": "Images",
    "pic": "Images",
    "picture": "Images",
    "design": "Images",
    "mockup": "Images",
    "illustration": "Images",
    "graphic": "Images",
    "thumbnail": "Images",
    "avatar": "Images",
    "profile": "Images",
    "cover": "Images",
    "poster": "Images",
    "flyer": "Images",
    "infographic": "Images",
    "diagram": "Images",
    "chart": "Images",
    "whatsapp image": "Images",  # WhatsApp pattern
    
    # Video-related keywords
    "video": "Videos",
    "movie": "Videos",
    "clip": "Videos",
    "recording": "Videos",
    "tutorial": "Videos",
    "screencast": "Videos",
    "webinar": "Videos",
    "stream": "Videos",
    "episode": "Videos",
    "trailer": "Videos",
    "vid": "Videos",
    "whatsapp video": "Videos",  # WhatsApp pattern
    
    # Audio-related keywords
    "song": "Audio",
    "music": "Audio",
    "podcast": "Audio",
    "audiobook": "Audio",
    "audio": "Audio",
    "voice": "Audio",
    "voicenote": "Audio",
    "recording": "Audio",
    "track": "Audio",
    "beat": "Audio",
    "ringtone": "Audio",
    "whatsapp audio": "Audio",  # WhatsApp pattern
    "whatsapp ptt": "Audio",  # WhatsApp voice note
    
    # Archive-related keywords
    "backup": "Archives",
    "archive": "Archives",
    "compressed": "Archives",
    "zipped": "Archives",
    "bundle": "Archives",
    "package": "Archives",
    
    # Code-related keywords
    "script": "Code",
    "source": "Code",
    "config": "Code",
    "settings": "Code",
    "env": "Code",
    "api": "Code",
    "sdk": "Code",
    "lib": "Code",
    "module": "Code",
    "component": "Code",
    
    # Executables
    "setup": "Executables",
    "installer": "Executables",
    "install": "Executables",
    "portable": "Executables",
    "crack": "Executables",
    "keygen": "Executables",
}


def classify_by_rules(filename: str) -> Optional[str]:
    """
    Classify a file based on keyword rules in the filename.
    
    This function checks if any known keywords appear in the filename
    (case-insensitive) and returns the corresponding category.
    
    Args:
        filename: The name of the file (with or without extension).
    
    Returns:
        Category name if a keyword match is found, None otherwise.
    
    Example:
        >>> classify_by_rules("invoice_2024.pdf")
        'Documents'
        >>> classify_by_rules("random_file.txt")
        None
    """
    filename_lower = filename.lower()
    
    # Check custom rules first (user-defined rules have highest priority)
    custom_rules = load_custom_rules()
    for keyword, category in custom_rules.items():
        if keyword in filename_lower:
            return category
    
    # Then check built-in rules
    for keyword, category in KEYWORD_RULES.items():
        if keyword in filename_lower:
            return category
    
    return None


def classify_by_extension(file_extension: str) -> str:
    """
    Classify a file based on its extension.
    
    Args:
        file_extension: The file extension (e.g., '.pdf', '.jpg').
    
    Returns:
        Category name or 'Other' if extension is not recognized.
    """
    ext = file_extension.lower()
    for category, extensions in FILE_CATEGORIES.items():
        if ext in extensions:
            return category
    return "Other"


def classify_file(filename: str, file_extension: str) -> str:
    """
    Classify a file using extension first, then keywords for ambiguous cases.
    
    This is the main classification function that should be used.
    It prioritizes extension-based classification to avoid false positives
    from keyword matching. Keywords are only used when the extension is
    unrecognized or for text-based files where context matters.
    
    Args:
        filename: The name of the file.
        file_extension: The file extension (e.g., '.pdf').
    
    Returns:
        The determined category for the file.
    
    Example:
        >>> classify_file("video_clip.jpg", ".jpg")
        'Images'  # Extension takes priority, avoids "clip" → Videos
        >>> classify_file("invoice.txt", ".txt")
        'Documents'  # Text file, keyword "invoice" refines category
        >>> classify_file("random_file.xyz", ".xyz")
        'Other'  # Unknown extension, no keyword match
    """
    # Check extension-based classification first
    ext_category = classify_by_extension(file_extension)
    
    # If extension gives a clear category (not Other), use it
    # Exception: for text-based files, allow keywords to refine
    ambiguous_extensions = {".log", ".md", ".csv", ".dat"}
    
    if ext_category != "Other" and file_extension.lower() not in ambiguous_extensions:
        return ext_category
    
    # For unknown extensions or ambiguous text files, try keyword rules
    keyword_category = classify_by_rules(filename)
    if keyword_category:
        return keyword_category
    
    # Fall back to extension result (could be "Other")
    return ext_category
