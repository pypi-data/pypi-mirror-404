# SFO File Organizer

A Python utility that automatically organizes files into categorized folders based on their file types, with support for rule-based classification, structured logging, and real-time monitoring.

## Features

- 📁 **Smart Classification**
  - **Rule-based classification** (keywords take priority)
  - **Extension-based fallback** classification (supports PHP, TS, JSX, etc.)
- ⚙️ **Customizable Categories** - Easy to add custom file categories and rules
- 🔄 **Duplicate Handling** - Automatic renaming for duplicate filenames
- 📊 **Statistics** - Summary report after organization
- 🧪 **Dry-Run Mode** - Preview changes without moving files
- 📝 **Structured Logging** - Console and file logging with configurable levels
- 🖥️ **Modern Desktop UI** - Sleek dark-themed interface with:
  - **Scheduling**: Automate organization to run daily.
  - **Flatten Directory**: Undo organization by moving files back to the root (only targets organizer-created folders).
  - **Watch Mode**: Real-time folder monitoring.
- ↩️ **Undo Support** - Easily revert any organization session (auto-cleans empty folders)
- 🧠 **Smart Context** - Auto-detects folder purpose by name (Photos, Documents, etc.) for specialized sorting

## Platform Compatibility

| Platform    | Pre-built Executable             | Run from Source |
| ----------- | -------------------------------- | --------------- |
| **Windows** | ✅ `.exe` available              | ✅ Supported    |
| **macOS**   | ✅ Available via GitHub Releases | ✅ Supported    |
| **Linux**   | ✅ Available via GitHub Releases | ✅ Supported    |

> **Note:** Pre-built executables for all platforms are automatically generated via GitHub Actions and attached to each [Release](https://github.com/pjames-tech/sfo-file-organizer/releases).

### macOS / Linux Setup

1. **Install Python 3.8+** (usually pre-installed on Linux, download from [python.org](https://python.org) for macOS)

2. **Clone and install dependencies:**

   ```bash
   git clone https://github.com/pjames-tech/sfo-file-organizer.git
   cd sfo-file-organizer
   pip install -r requirements.txt
   ```

3. **Run the GUI:**

   ```bash
   python gui.py
   ```

4. **Or run the CLI:**

   ```bash
   python organizer.py --source ~/Downloads
   ```

### Building Your Own Executable (Optional)

If you want to create a native executable for your platform:

```bash
# Install PyInstaller
pip install pyinstaller

# Build the executable
pyinstaller --onefile --windowed gui.py
```

The executable will be created in the `dist/` folder.

## Architecture

```text
sfo-file-organizer/
├── organizer.py        # Main CLI and orchestration
├── gui.py              # Desktop GUI application (tkinter)
├── app_config.py       # Configuration and file categories
├── rules.py            # Rule-based classification engine
├── scheduler.py        # Windows Task Scheduler integration
├── history.py          # Undo/redo history management
├── logging_config.py   # Logging configuration
├── run_organizer.bat   # Batch script helper
├── requirements.txt    # Dependencies
└── tests/              # Unit tests
```

### Classification Priority

1. **Keyword Rules** - Custom rules take priority.
2. **File Extension** - Standard classification based on file type.

## Installation

### Option 1: Install via pip (Recommended for all platforms)

```bash
pip install sfo-file-organizer
```

Then run:

```bash
sfo-file-organizer        # Launch GUI
sfo                       # Shortcut for GUI
sfo-cli --source ~/Downloads  # CLI mode
```

### Option 2: Download Pre-built Executable

| Platform    | Download                                                                                                                                    |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| **Windows** | [SFO-File-Organizer-Windows.exe](https://github.com/pjames-tech/sfo-file-organizer/releases/latest/download/SFO-File-Organizer-Windows.exe) |
| **macOS**   | [SFO-File-Organizer-macOS.zip](https://github.com/pjames-tech/sfo-file-organizer/releases/latest/download/SFO-File-Organizer-macOS.zip)     |
| **Linux**   | [SFO-File-Organizer-Linux](https://github.com/pjames-tech/sfo-file-organizer/releases/latest/download/SFO-File-Organizer-Linux)             |

### Option 3: Run from Source

```bash
git clone https://github.com/pjames-tech/sfo-file-organizer.git
cd sfo-file-organizer
pip install -r requirements.txt
python gui.py
```

## Usage

### Quick Start

1. **Install** using one of the methods above.
2. **Launch** the application (GUI or CLI).
3. **Select** the folder you want to organize.
4. **Click "Organize Now"** and watch your files get sorted!

## 👁️ Watch Mode

Watch Mode monitors your source folder in real-time. Any file you drop into the folder will be automatically categorized and moved instantly.

- **GUI**: Just toggle the **"Watch Mode"** switch.
- **CLI**: Run `python organizer.py --watch`

### Desktop GUI

Launch the graphical interface:

```bash
python gui.py
```

**Features:**

- 📂 Browse and select any folder to organize
- 🚀 **Organize Now** - One-click file organization
- 👁️ **Preview Changes** - See what will happen before committing
- 🧹 **Flatten** - Move files out of organizer-created subfolders back to the root (preserves pre-existing folders)
- ⏰ **Automation** - Schedule daily organization tasks
- ↩️ **Undo Last** - Restore files to their original locations and clean up empty folders
- 📋 Activity log with colored output
- 🧠 **Smart Context** - Enable to sort images by year or documents by type based on folder name
- ⌚ **Watch Mode** - Real-time folder monitoring

### CLI Mode

```bash
# Organize Downloads folder (in-place)
python organizer.py --source ~/Downloads

# Dry-run (preview without moving files)
python organizer.py --dry-run --source ~/Downloads

# Undo last organization
python organizer.py --undo

# View history
python organizer.py --history
```

### CLI Options

| Flag            | Short | Description                                     |
| --------------- | ----- | ----------------------------------------------- |
| `--source`      | `-s`  | Source directory to organize                    |
| `--dest`        | `-d`  | Destination directory (default: same as source) |
| `--dry-run`     | `-n`  | Preview changes without moving files            |
| `--in-place`    | `-i`  | Organize within source folder (default)         |
| `--watch`       | `-w`  | Monitor folder and organize in real-time        |
| `--undo`        |       | Undo the last organization                      |
| `--history`     |       | Show organization history                       |
| `--log-level`   | `-l`  | Set logging level (DEBUG, INFO, WARNING, ERROR) |
| `--no-log-file` |       | Disable logging to file                         |

### Examples

```bash
# Preview what would happen
python organizer.py --dry-run --source ./messy_folder

# Quick organize current downloads
python organizer.py --source ~/Downloads

# Start watching a folder
python organizer.py --watch --source ~/Downloads
```

## Configuration

### File Categories (`app_config.py`)

```python
FILE_CATEGORIES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ...],
    "Documents": [".pdf", ".doc", ".docx", ".txt", ...],
    "Videos": [".mp4", ".mkv", ".avi", ...],
    "Code": [".py", ".js", ".php", ".ts", ".jsx", ...],
    # Add custom categories here
}
```

### Keyword Rules (`rules.py`)

```python
KEYWORD_RULES = {
    "invoice": "Documents",    # Files with "invoice" go to Documents
    "screenshot": "Images",    # Files with "screenshot" go to Images
    # Add custom rules here
}
```

## Testing

```bash
# Install pytest
pip install pytest

# Run all tests
pytest tests/ -v
```

## Automatic Scheduling (Windows Task Scheduler)

Run the organizer automatically on a schedule using the included batch script.

### Quick Setup

1. **Edit `run_organizer.bat`** to customize your source/destination folders:

   ```batch
   "C:\Python314\python.exe" organizer.py --source "%USERPROFILE%\Downloads" --dest "%USERPROFILE%\Downloads" --log-level INFO
   ```

2. **Create the scheduled task** (run in PowerShell as admin):

   ```powershell
   schtasks /create /tn "Smart File Organizer" /tr "C:\path\to\run_organizer.bat" /sc daily /st 12:00 /f
   ```

## License

MIT License
