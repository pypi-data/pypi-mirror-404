"""
SFO File Organizer
Automatically organizes files in a directory based on their types.

Features:
- Rule-based classification (keywords take priority)
- Extension-based fallback classification
- Structured logging with configurable levels
- Dry-run mode for safe previewing
- CLI with backward-compatible interactive mode
"""

import os
import sys
import shutil
import argparse
from pathlib import Path
from typing import Optional
import time
from datetime import datetime

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False

from app_config import FILE_CATEGORIES, DEFAULT_SOURCE_DIR, DEFAULT_DEST_DIR, DETAILED_CATEGORIES
from logging_config import setup_logging, get_logger
from rules import classify_file, classify_by_rules
from history import start_session, record_movement, save_session, undo_last_session, get_history_summary

# Hidden marker file to identify folders created by the organizer
ORGANIZER_MARKER = ".sfo_organized"


def get_category(file_extension: str) -> str:
    """
    Determine the category of a file based on its extension.
    
    Args:
        file_extension: The file extension (e.g., '.pdf', '.jpg')
    
    Returns:
        The category name or 'Other' if not found.
    
    Note:
        This function is preserved for backward compatibility.
        For new code, use classify_file() from rules.py instead.
    """
    ext = file_extension.lower()
    for category, extensions in FILE_CATEGORIES.items():
        if ext in extensions:
            return category
    return "Other"


def detect_folder_context(source_path: Path) -> str:
    """
    Analyze folder to determine its primary context.
    First checks the folder name, then falls back to file content analysis.
    Returns: 'Images', 'Documents', or 'Mixed'
    """
    # First, check the folder name for context hints
    folder_name = source_path.name.lower()
    
    # Generic folders that should use standard (Mixed) sorting - no special context
    generic_folder_names = ['downloads', 'desktop', 'temp', 'tmp', 'new folder']
    for name in generic_folder_names:
        if name in folder_name:
            return "Mixed"
    
    # Common folder names that indicate image context
    image_folder_names = ['photos', 'pictures', 'images', 'screenshots', 'camera', 
                          'dcim', 'wallpapers', 'gallery', 'pics']
    
    # Common folder names that indicate document context
    document_folder_names = ['documents', 'docs', 'papers', 'reports', 'invoices',
                             'contracts', 'receipts', 'pdfs', 'work', 'office']
    
    # Check folder name first
    for name in image_folder_names:
        if name in folder_name:
            return "Images"
    
    for name in document_folder_names:
        if name in folder_name:
            return "Documents"
    
    # Fall back to analyzing file contents
    counts = {"Images": 0, "Documents": 0, "Total": 0}
    
    for item in source_path.iterdir():
        if item.is_file():
            counts["Total"] += 1
            ext = item.suffix.lower()
            if ext in FILE_CATEGORIES["Images"]:
                counts["Images"] += 1
            elif ext in FILE_CATEGORIES["Documents"]:
                counts["Documents"] += 1
    
    if counts["Total"] == 0:
        return "Mixed"
        
    img_ratio = counts["Images"] / counts["Total"]
    doc_ratio = counts["Documents"] / counts["Total"]
    
    if img_ratio > 0.6:
        return "Images"
    elif doc_ratio > 0.6:
        return "Documents"
    return "Mixed"

def get_detailed_category(file_path: Path, context: str) -> str:
    """Get specialized category based on context."""
    if context == "Documents":
        # Check detailed mapping first
        ext = file_path.suffix.lower()
        if ext in DETAILED_CATEGORIES:
            return DETAILED_CATEGORIES[ext]
            
    elif context == "Images":
        # Only sort actual images by year
        ext = file_path.suffix.lower()
        if ext in FILE_CATEGORIES["Images"]:
            # Sort by Year (creation date)
            try:
                mtime = os.path.getmtime(file_path)
                dt = datetime.fromtimestamp(mtime)
                return str(dt.year)
            except Exception:
                pass
            
    return None

def organize_files(
    source_dir: Optional[str] = None,
    dest_dir: Optional[str] = None,
    dry_run: bool = False,
    use_ai: bool = False,
    smart_context: bool = False
) -> dict:
    """
    Organize files from source directory into categorized folders.
    
    Args:
        source_dir: Directory containing files to organize.
        dest_dir: Directory where organized folders will be created.
        dry_run: If True, only log actions without moving files.
        use_ai: If True, attempt AI classification (requires API setup).
        smart_context: If True, adapt organization strategy based on folder content.
    
    Returns:
        Dictionary with statistics about organized files:
        - moved: Number of files successfully moved
        - skipped: Number of directories skipped
        - errors: Number of errors encountered
    
    Raises:
        FileNotFoundError: If source directory does not exist.
        PermissionError: If lacking permissions to read source or write dest.
    """
    logger = get_logger()
    
    source = Path(source_dir or DEFAULT_SOURCE_DIR)
    destination = Path(dest_dir or DEFAULT_DEST_DIR)
    
    # Validate source directory
    if not source.exists():
        logger.error(f"Source directory not found: {source}")
        raise FileNotFoundError(f"Source directory not found: {source}")
    
    if not source.is_dir():
        logger.error(f"Source path is not a directory: {source}")
        raise NotADirectoryError(f"Source path is not a directory: {source}")
    
    # Check read permissions
    if not os.access(source, os.R_OK):
        logger.error(f"Permission denied: Cannot read from {source}")
        raise PermissionError(f"Permission denied: Cannot read from {source}")
    
    stats = {"moved": 0, "skipped": 0, "errors": 0}
    
    # Context detection
    context = "Mixed"
    if smart_context:
        context = detect_folder_context(source)
        logger.info(f"Smart Context detected: {context}")
    
    # Start a session for undo support
    session = start_session(str(source), str(destination), dry_run)
    
    logger.info(f"{'[DRY RUN] ' if dry_run else ''}Organizing files from: {source}")
    logger.info(f"{'[DRY RUN] ' if dry_run else ''}Destination: {destination}")
    
    for file_path in source.iterdir():
        if file_path.is_file():
            try:
                # Determine category using the classification chain
                category = None
                
                # 0. Smart Context Strategy
                if smart_context and context != "Mixed":
                    category = get_detailed_category(file_path, context)
                    if category:
                        logger.debug(f"Smart Context ({context}) matched {file_path.name} -> {category}")

                # 1. Fall back to rule-based + extension classification
                if not category:
                    category = classify_file(file_path.name, file_path.suffix)
                    if context == "Mixed": # Only log rule matches in mixed mode to reduce noise
                        rule_match = classify_by_rules(file_path.name)
                        if rule_match:
                            logger.debug(f"Rule matched {file_path.name} -> {category}")
                        else:
                            logger.debug(f"Extension matched {file_path.name} -> {category}")
                
                category_dir = destination / category
                
                if not dry_run:
                    category_dir.mkdir(parents=True, exist_ok=True)
                    # Mark this folder as created by the organizer
                    marker_path = category_dir / ORGANIZER_MARKER
                    if not marker_path.exists():
                        marker_path.touch()
                        # Make the marker hidden on Windows
                        if os.name == 'nt':
                            try:
                                import ctypes
                                ctypes.windll.kernel32.SetFileAttributesW(str(marker_path), 2)
                            except Exception:
                                pass  # Silently ignore if we can't set attributes
                
                dest_path = category_dir / file_path.name
                
                # Handle duplicate filenames
                if dest_path.exists() or (not dry_run and dest_path.exists()):
                    base = file_path.stem
                    ext = file_path.suffix
                    counter = 1
                    while dest_path.exists():
                        dest_path = category_dir / f"{base}_{counter}{ext}"
                        counter += 1
                    logger.warning(f"Duplicate found, renaming to: {dest_path.name}")
                
                if dry_run:
                    logger.info(f"[DRY RUN] Would move: {file_path.name} -> {category}/")
                else:
                    # Record the movement before moving
                    original_path = str(file_path)
                    shutil.move(str(file_path), str(dest_path))
                    record_movement(session, original_path, str(dest_path))
                    logger.info(f"Moved: {file_path.name} -> {category}/")
                
                stats["moved"] += 1
                
            except PermissionError as e:
                logger.error(f"Permission denied for {file_path.name}: {e}")
                stats["errors"] += 1
            except OSError as e:
                logger.error(f"OS error moving {file_path.name}: {e}")
                stats["errors"] += 1
            except Exception as e:
                logger.error(f"Unexpected error moving {file_path.name}: {e}")
                stats["errors"] += 1
        else:
            logger.debug(f"Skipped directory: {file_path.name}")
            stats["skipped"] += 1
    
    # Save session for undo support
    save_session(session)
    
    return stats


def flatten_directory(source_dir: str) -> dict:
    """
    Move all files from organizer-created subdirectories back to the source root.
    Only flattens folders that contain the .sfo_organized marker file.
    Records operations for Undo.
    """
    logger = get_logger()
    source = Path(source_dir)
    stats = {"moved": 0, "errors": 0, "removed_dirs": 0, "skipped_dirs": 0}
    
    if not source.exists() or not source.is_dir():
        logger.error(f"Invalid source directory: {source}")
        return stats

    # Find all subdirectories that have the organizer marker (first level only)
    tagged_dirs = [d for d in source.iterdir() 
                   if d.is_dir() and (d / ORGANIZER_MARKER).exists()]
    
    if not tagged_dirs:
        logger.info("No organizer-created folders found to flatten.")
        return stats
    
    # Count pre-existing (untagged) directories for logging
    all_subdirs = [d for d in source.iterdir() if d.is_dir()]
    untagged_count = len(all_subdirs) - len(tagged_dirs)
    if untagged_count > 0:
        logger.info(f"Preserving {untagged_count} pre-existing folder(s).")
        stats["skipped_dirs"] = untagged_count

    # Start session for Undo
    session = start_session(str(source), str(source), dry_run=False)
    
    # Get files only from tagged directories (recursive within those dirs)
    files = []
    for tagged_dir in tagged_dirs:
        files.extend([p for p in tagged_dir.rglob("*") 
                      if p.is_file() and p.name != ORGANIZER_MARKER])
    
    for file_path in files:
        try:
            dest_path = source / file_path.name
            
            # Handle duplicates
            if dest_path.exists():
                base = file_path.stem
                ext = file_path.suffix
                counter = 1
                while dest_path.exists():
                    dest_path = source / f"{base}_{counter}{ext}"
                    counter += 1
            
            original_path = str(file_path)
            shutil.move(str(file_path), str(dest_path))
            
            # Record for undo
            record_movement(session, original_path, str(dest_path))
            
            stats["moved"] += 1
            logger.info(f"Flattened: {file_path.name}")
            
        except Exception as e:
            logger.error(f"Error moving {file_path}: {e}")
            stats["errors"] += 1
    
    # Remove tagged directories (including marker files) - bottom-up
    for tagged_dir in tagged_dirs:
        # First remove the marker file
        marker_path = tagged_dir / ORGANIZER_MARKER
        try:
            if marker_path.exists():
                marker_path.unlink()
        except Exception:
            pass
        
        # Remove any empty subdirectories within the tagged dir (bottom-up)
        for dir_path in sorted(tagged_dir.rglob("*"), key=lambda p: len(p.parts), reverse=True):
            if dir_path.is_dir():
                try:
                    if not any(dir_path.iterdir()):
                        dir_path.rmdir()
                        stats["removed_dirs"] += 1
                        logger.info(f"Removed empty dir: {dir_path}")
                except Exception:
                    pass
        
        # Finally remove the tagged directory itself if empty
        try:
            if not any(tagged_dir.iterdir()):
                tagged_dir.rmdir()
                stats["removed_dirs"] += 1
                logger.info(f"Removed organizer dir: {tagged_dir.name}")
        except Exception as e:
            logger.warning(f"Could not remove {tagged_dir.name}: {e}")
    
    # Save the session
    save_session(session)
    return stats


class OrganizerHandler(FileSystemEventHandler):
    """Handles file system events by triggering organization."""
    
    def __init__(self, source_dir: str, dest_dir: str, use_ai: bool, smart_context: bool = False):
        self.source_dir = source_dir
        self.dest_dir = dest_dir
        self.use_ai = use_ai
        self.smart_context = smart_context
        self.logger = get_logger()
        # Coalescing: don't organize too frequently
        self.last_run = 0
        self.cooldown = 2 # seconds
        
    def on_created(self, event):
        if not event.is_directory:
            self._trigger_organize()
            
    def on_moved(self, event):
        if not event.is_directory and Path(event.dest_path).parent == Path(self.source_dir):
            self._trigger_organize()

    def _trigger_organize(self):
        current_time = time.time()
        if current_time - self.last_run > self.cooldown:
            self.last_run = current_time
            # Wait a tiny bit for the file to be fully written/unlocked
            time.sleep(0.5)
            try:
                self.logger.info("Watch Mode: Change detected, organizing...")
                organize_files(self.source_dir, self.dest_dir, use_ai=self.use_ai, smart_context=self.smart_context)
            except Exception as e:
                self.logger.error(f"Watch Mode Error: {e}")


def start_watch_mode(source_dir: str, dest_dir: str, use_ai: bool):
    """Start monitoring a directory for changes."""
    logger = get_logger()
    if not WATCHDOG_AVAILABLE:
        logger.error("watchdog library not installed. Install with: pip install watchdog")
        return False
        
    source = Path(source_dir)
    dest = Path(dest_dir) or source
    
    event_handler = OrganizerHandler(str(source), str(dest), use_ai)
    observer = Observer()
    observer.schedule(event_handler, str(source), recursive=False)
    
    logger.info(f"WATCH MODE ACTIVE: Monitoring {source}")
    logger.info("Press Ctrl+C to stop.")
    
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logger.info("Watch Mode stopped.")
    
    observer.join()
    return True


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="SFO File Organizer - Automatically organize files by type",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python organizer.py                           # Interactive mode
  python organizer.py --source ~/Downloads      # Specify source
  python organizer.py --dry-run                 # Preview without moving
  python organizer.py --log-level DEBUG         # Verbose logging
        """
    )
    
    parser.add_argument(
        "--source", "-s",
        type=str,
        default=None,
        help=f"Source directory to organize (default: {DEFAULT_SOURCE_DIR})"
    )
    
    parser.add_argument(
        "--dest", "-d",
        type=str,
        default=None,
        help=f"Destination directory for organized files (default: {DEFAULT_DEST_DIR})"
    )
    
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Preview changes without actually moving files"
    )
    
    parser.add_argument(
        "--in-place", "-i",
        action="store_true",
        help="Organize files within the source folder (creates subfolders in source)"
    )
    

    
    parser.add_argument(
        "--log-level", "-l",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--no-log-file",
        action="store_true",
        help="Disable logging to file"
    )
    
    parser.add_argument(
        "--undo",
        action="store_true",
        help="Undo the last organization operation"
    )
    
    parser.add_argument(
        "--history",
        action="store_true",
        help="Show organization history and exit"
    )
    
    parser.add_argument(
        "--watch", "-w",
        action="store_true",
        help="Run in Watch Mode: monitor source folder and organize new files in real-time"
    )
    
    return parser.parse_args()


def main() -> int:
    """
    Main entry point for the file organizer.
    
    Returns:
        Exit code (0 for success, 1 for errors).
    """
    args = parse_args()
    
    # Setup logging
    log_file = None if args.no_log_file else "organizer.log"
    setup_logging(level=args.log_level, log_file=log_file)
    logger = get_logger()
    
    print("=" * 50)
    print("SFO File Organizer")
    print("=" * 50)
    
    print("SFO File Organizer")
    print("=" * 50)
    
    # Handle --undo flag
    if args.undo:
        print("\nUndoing last organization...")
        result = undo_last_session()
        if result["success"]:
            print(f"\n✅ Restored {result['restored']} files")
            if result["errors"] > 0:
                print(f"⚠️  {result['errors']} files could not be restored")
        else:
            print(f"\n❌ {result['message']}")
        print("=" * 50)
        return 0 if result.get("success", False) else 1
    
    # Handle --history flag
    if args.history:
        history = get_history_summary()
        if not history:
            print("\nNo organization history found.")
        else:
            print("\nOrganization History:")
            print("-" * 50)
            for i, session in enumerate(reversed(history), 1):
                status = "✓" if not session["undone"] else "↩ (undone)"
                dry = " [dry-run]" if session["dry_run"] else ""
                print(f"{i}. {session['timestamp'][:16]} - {session['files_moved']} files {status}{dry}")
            print("-" * 50)
        print("=" * 50)
        return 0
    
    # Use CLI args or fall back to interactive prompts (backward compatibility)
    source = args.source
    dest = args.dest
    
    # Handle --in-place flag (organize within source folder)
    if args.in_place:
        if source is None:
            source = DEFAULT_SOURCE_DIR
        dest = source  # Set destination to same as source
        print(f"[IN-PLACE MODE] Organizing within: {source}")
    
    if source is None and dest is None and not args.dry_run and not args.in_place:
        # Check if running in a non-interactive environment
        if sys.stdin is None:
            print("Error: Running in non-interactive mode without arguments.")
            print("Please provide --source and --dest arguments.")
            return 1

        # Interactive mode - maintain backward compatibility
        source = input(f"Source directory [{DEFAULT_SOURCE_DIR}]: ").strip() or None
        dest = input(f"Destination directory [{DEFAULT_DEST_DIR}]: ").strip() or None
    
    if args.dry_run:
        print("\n[DRY RUN MODE] No files will be moved.\n")
    
    if args.watch:
        if not WATCHDOG_AVAILABLE:
            print("\n❌ Error: 'watchdog' library is required for Watch Mode.")
            print("Install it with: pip install watchdog")
            return 1
        
        try:
            start_watch_mode(source, dest or source, False)
            return 0
        except Exception as e:
            print(f"\n❌ Error starting Watch Mode: {e}")
            return 1

    print("\nOrganizing files...")
    
    try:
        stats = organize_files(
            source_dir=source,
            dest_dir=dest,
            dry_run=args.dry_run,
            use_ai=False
        )
        
        print("\n" + "=" * 50)
        print("Summary:")
        print(f"  Files {'to move' if args.dry_run else 'moved'}: {stats['moved']}")
        print(f"  Skipped (directories): {stats['skipped']}")
        print(f"  Errors: {stats['errors']}")
        print("=" * 50)
        
        return 0 if stats["errors"] == 0 else 1
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("Please check that the source directory exists and try again.")
        return 1
    except PermissionError as e:
        print(f"\n❌ Error: {e}")
        print("Please check your permissions and try again.")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        print(f"\n❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
