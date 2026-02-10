# Architecture

This document describes the architecture of SnipOCR after the refactoring.

## Project Structure

```
SnipOCR/
├── main.py                      # Minimal entry point
├── snip_ocr/                    # Main package
│   ├── __init__.py             # Package initialization, version info
│   ├── constants.py            # Application constants and settings
│   ├── config.py               # Configuration management (token, model)
│   ├── updater.py              # Automatic update checking and installation
│   ├── worker.py               # AI worker thread for cloud OCR processing
│   ├── local_worker.py         # Local OCR worker using PaddleOCR
│   ├── model_downloader.py     # Model download and management
│   ├── manager.py              # Main application manager
│   └── ui/                     # UI components
│       ├── __init__.py
│       ├── settings_dialog.py  # Settings dialog
│       ├── model_dialog.py     # Model management dialog
│       ├── snipper.py          # Screenshot overlay widget
│       └── update_dialog.py    # Update progress dialog
├── icon.png                     # Application icon
├── pyproject.toml              # Project configuration
└── snip_ocr.spec               # PyInstaller specification
```

## Module Responsibilities

### `main.py`
- Entry point for the application
- Sets up environment variables for Qt
- Imports and runs the Manager

### `snip_ocr/__init__.py`
- Package initialization
- Exports version information

### `snip_ocr/constants.py`
- Defines application constants
- API endpoints and configuration
- Language mappings
- System prompts

### `snip_ocr/config.py`
- Configuration file management
- Load/save GitHub token and model preferences
- Platform-specific config paths

### `snip_ocr/updater.py`
- `UpdateChecker` class: Checks GitHub releases for new versions
- Version comparison logic
- Download and installation of updates
- Platform-specific installer handling

### `snip_ocr/worker.py`
- `AIWorker` class: Background thread for cloud AI API calls
- Handles retries and error recovery
- Processes screenshots through GitHub Models API (GPT-4o/GPT-4o-mini)

### `snip_ocr/local_worker.py`
- `LocalOCRWorker` class: Background thread for local OCR processing
- Uses PaddleOCR for offline text recognition
- Hardware detection (CPU/CUDA/XPU)
- Converts OCR results to Markdown with LaTeX

### `snip_ocr/model_downloader.py`
- Model download and management functions
- Checks if PaddleOCR models are downloaded
- Triggers model initialization and download
- Model size estimation

### `snip_ocr/manager.py`
- `Manager` class: Main application controller
- Coordinates all components:
  - System tray icon and menu
  - Hotkey listener (pynput)
  - Screenshot capture (Snipper)
  - AI processing (AIWorker for cloud, LocalOCRWorker for local)
  - Update checking (UpdateChecker)
- Handles application lifecycle
- Routes processing to appropriate worker based on model selection

### `snip_ocr/ui/settings_dialog.py`
- `SettingsDialog` class: Configuration UI
- GitHub token input (optional for local model)
- Model selection (cloud vs local)
- Disables token requirement when local model selected

### `snip_ocr/ui/model_dialog.py`
- `ModelDialog` class: Model management UI
- Shows model download status
- Downloads PaddleOCR models with progress bar
- Model deletion option

### `snip_ocr/ui/snipper.py`
- `Snipper` class: Full-screen overlay for region selection
- Click-and-drag screenshot capture
- Multi-monitor support

### `snip_ocr/ui/update_dialog.py`
- `UpdateDialog` class: Update download/installation UI
- Shows download progress
- Handles installation process

## Data Flow

### Screenshot Capture Flow (Cloud Models)
1. User presses `Ctrl+Shift+S` (or clicks tray icon)
2. `Manager` receives trigger signal
3. `Snipper` overlay displays
4. User selects region
5. `Snipper` captures screenshot, converts to base64
6. `Manager` creates `AIWorker` in background thread
7. `AIWorker` sends image to GitHub Models API
8. Result copied to clipboard
9. Notification displayed

### Screenshot Capture Flow (Local Model)
1. User presses `Ctrl+Shift+S` (or clicks tray icon)
2. `Manager` receives trigger signal
3. `Snipper` overlay displays
4. User selects region
5. `Snipper` captures screenshot, converts to base64
6. `Manager` saves image to temporary file
7. `Manager` creates `LocalOCRWorker` in background thread
8. `LocalOCRWorker` initializes PaddleOCR with hardware detection
9. PaddleOCR processes image locally (CPU/GPU/XPU)
10. OCR results converted to Markdown with LaTeX formatting
11. Result copied to clipboard
12. Temporary file cleaned up
13. Notification displayed

### Update Check Flow
1. Application starts, `Manager` initializes
2. `Manager` creates `UpdateChecker` instance
3. `UpdateChecker` queries GitHub API for latest release
4. If newer version found:
   - "Update Available" menu item becomes visible
   - Notification displayed (clickable)
5. User clicks notification or menu item
6. `UpdateDialog` displays and downloads update
7. User chooses to install now or later
8. If installing now, application closes and installer runs

### Model Download Flow
1. User selects **local-paddleocr** model in Settings
2. User opens **Manage Models** from tray menu
3. `ModelDialog` checks if models are downloaded via `is_model_downloaded()`
4. If not downloaded, user clicks "Download Models"
5. Confirmation dialog shown (~150 MB download)
6. `ModelDownloadWorker` thread starts
7. PaddleOCR initialized, triggering auto-download of models
8. Progress bar updates during download
9. Models cached in `~/.paddlex/official_models/`
10. Marker file created in app config directory
11. Success notification displayed
12. Local OCR now ready for offline use

## Configuration

Configuration is stored in:
- **Windows**: `%APPDATA%/SnipOCR/config.json`
- **macOS/Linux**: `~/.config/SnipOCR/config.json`

Example `config.json`:
```json
{
  "github_token": "ghp_xxxxxxxxxxxxx",
  "model": "gpt-4o"
}
```

Or for local model (no token required):
```json
{
  "model": "local-paddleocr"
}
```

Model files are stored separately:
- **PaddleOCR cache**: `~/.paddlex/official_models/`
- **App marker file**: `%APPDATA%/SnipOCR/models/.models_ready` (Windows) or `~/.config/SnipOCR/models/.models_ready` (macOS/Linux)

## Dependencies

### Runtime Dependencies
- `PyQt6`: GUI framework
- `pynput`: Global hotkey capture
- `pyperclip`: Clipboard operations
- `requests`: HTTP requests (AI API, update checking)
- `pillow`: Image processing
- `paddleocr`: Local OCR engine
- `paddlepaddle`: Deep learning framework for PaddleOCR

### Development Dependencies
- `pyinstaller`: Creates standalone executables
- `ruff`: Linting and formatting

## Building

### Development
```bash
# Install dependencies
uv sync

# Run application
uv run main.py
```

### Production Build
```bash
# Build executable
uv run pyinstaller snip_ocr.spec

# Create installer (Windows, requires Inno Setup)
make installer
```

## Extension Points

### Adding a New UI Component
1. Create new file in `snip_ocr/ui/`
2. Import in `manager.py`
3. Connect signals as needed

### Adding a New Configuration Option
1. Update `config.py` with load/save functions
2. Update `constants.py` if needed
3. Update `SettingsDialog` in `snip_ocr/ui/settings_dialog.py`

### Adding a New Feature to System Tray
1. Update `Manager._setup_tray()` in `manager.py`
2. Add QAction and connect to handler method
3. Implement handler method in `Manager` class
