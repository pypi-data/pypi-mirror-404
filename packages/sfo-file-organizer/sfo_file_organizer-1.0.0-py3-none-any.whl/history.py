"""
History tracking module for SFO File Organizer.

Tracks file movements to enable undo functionality.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from datetime import datetime
from typing import Optional
from app_config import DATA_DIR

logger = logging.getLogger("smart_file_organizer")

# History file location
HISTORY_FILE = DATA_DIR / "organizer_history.json"
MAX_HISTORY_SESSIONS = 10  # Keep last 10 sessions


def load_history() -> dict:
    """Load history from JSON file."""
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load history: {e}")
    return {"sessions": []}


def save_history(data: dict) -> None:
    """Save history to JSON file."""
    try:
        # Keep only the last N sessions
        if len(data["sessions"]) > MAX_HISTORY_SESSIONS:
            data["sessions"] = data["sessions"][-MAX_HISTORY_SESSIONS:]
        
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.warning(f"Could not save history: {e}")


def start_session(source_dir: str, dest_dir: str, dry_run: bool = False) -> dict:
    """
    Start a new organization session.
    
    Args:
        source_dir: Source directory path.
        dest_dir: Destination directory path.
        dry_run: Whether this is a dry run (not saved to history).
    
    Returns:
        Session dictionary to track movements.
    """
    return {
        "timestamp": datetime.now().isoformat(),
        "source_dir": source_dir,
        "dest_dir": dest_dir,
        "dry_run": dry_run,
        "movements": [],
        "completed": False
    }


def record_movement(session: dict, original_path: str, new_path: str) -> None:
    """
    Record a file movement in the session.
    
    Args:
        session: Current session dictionary.
        original_path: Original file path (before move).
        new_path: New file path (after move).
    """
    session["movements"].append({
        "from": original_path,
        "to": new_path
    })


def save_session(session: dict) -> None:
    """
    Save a completed session to history.
    
    Args:
        session: Session dictionary to save.
    """
    if session.get("dry_run"):
        logger.debug("Dry run session - not saving to history")
        return
    
    if not session["movements"]:
        logger.debug("No movements to save")
        return
    
    session["completed"] = True
    
    history = load_history()
    history["sessions"].append(session)
    save_history(history)
    
    logger.info(f"Session saved with {len(session['movements'])} movements")


def get_last_session() -> Optional[dict]:
    """
    Get the most recent session that can be undone.
    
    Returns:
        Last session dictionary or None if no sessions exist.
    """
    history = load_history()
    
    # Find the last completed, non-dry-run session
    for session in reversed(history["sessions"]):
        if session.get("completed") and not session.get("dry_run"):
            if not session.get("undone"):
                return session
    
    return None


def undo_last_session() -> dict:
    """
    Undo the last organization session.
    
    Returns:
        Statistics about the undo operation.
    """
    import shutil
    
    session = get_last_session()
    
    if not session:
        logger.warning("No session to undo")
        return {"success": False, "message": "No session to undo", "restored": 0, "errors": 0}
    
    stats = {"success": True, "restored": 0, "errors": 0, "movements": []}
    
    logger.info(f"Undoing session from {session['timestamp']}")
    print(f"\nUndoing organization from {session['timestamp']}")
    print(f"Restoring {len(session['movements'])} files...")
    
    # Reverse the movements
    for movement in reversed(session["movements"]):
        original_path = Path(movement["from"])
        current_path = Path(movement["to"])
        
        try:
            if current_path.exists():
                # Ensure original directory exists
                original_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Move file back
                shutil.move(str(current_path), str(original_path))
                logger.info(f"Restored: {current_path.name} -> {original_path.parent}")
                print(f"  Restored: {current_path.name}")
                stats["restored"] += 1
                stats["movements"].append({
                    "from": str(current_path),
                    "to": str(original_path)
                })
            else:
                logger.warning(f"File not found (may have been moved/deleted): {current_path}")
                stats["errors"] += 1
                
        except Exception as e:
            logger.error(f"Error restoring {current_path}: {e}")
            stats["errors"] += 1
    
    # Mark session as undone
    history = load_history()
    for s in history["sessions"]:
        if s["timestamp"] == session["timestamp"]:
            s["undone"] = True
            s["undo_timestamp"] = datetime.now().isoformat()
            break
    save_history(history)
    
    # Clean up empty category directories (including nested ones and marker files)
    dest_dir = Path(session["dest_dir"])
    if dest_dir.exists():
        # First pass: remove marker files from empty directories
        for marker_file in dest_dir.rglob(".sfo_organized"):
            try:
                parent = marker_file.parent
                # Check if directory only contains the marker file
                contents = list(parent.iterdir())
                if len(contents) == 1 and contents[0].name == ".sfo_organized":
                    marker_file.unlink()
                    logger.debug(f"Removed marker file: {marker_file}")
            except Exception:
                pass
        
        # Second pass: remove empty directories (bottom-up)
        dirs_to_check = sorted(dest_dir.rglob("*"), key=lambda p: len(p.parts), reverse=True)
        removed_count = 0
        for dir_path in dirs_to_check:
            if dir_path.is_dir():
                try:
                    if not any(dir_path.iterdir()):
                        dir_path.rmdir()
                        removed_count += 1
                        logger.debug(f"Removed empty directory: {dir_path}")
                except Exception:
                    pass
        
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} empty directories")
    
    return stats


def get_history_summary() -> list:
    """
    Get a summary of all sessions in history.
    
    Returns:
        List of session summaries.
    """
    history = load_history()
    summaries = []
    
    for session in history["sessions"]:
        summaries.append({
            "timestamp": session["timestamp"],
            "source": session["source_dir"],
            "dest": session["dest_dir"],
            "files_moved": len(session["movements"]),
            "undone": session.get("undone", False),
            "dry_run": session.get("dry_run", False)
        })
    
    return summaries


def clear_history() -> None:
    """Clear all history."""
    save_history({"sessions": []})
    logger.info("History cleared")
