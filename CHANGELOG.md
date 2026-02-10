# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Offline Local OCR Mode**: New `local-paddleocr` model for completely offline operation
  - Uses PaddleOCR for local text recognition
  - No GitHub Token required when using local model
  - Hardware acceleration support (CPU, CUDA GPU, Intel ARC XPU)
  - Automatic model download (~150 MB) on first use
  - Models cached in `~/.paddlex/` directory
- **Model Management UI**: New "Manage Models" menu option
  - Download/initialize local OCR models
  - View model download status and size
  - Progress bar during model download
  - Option to reset/re-download models
- **Automatic Update System**: Application now checks for updates on startup via GitHub Releases
  - Clickable notification when updates are available
  - Progress dialog showing download and installation status
  - "Update Available" menu item in system tray (visible only when updates are available)
  - Support for Windows (.exe, .msi) and macOS (.dmg) installers

### Changed
- **Settings Dialog**: Updated to support local model
  - GitHub Token field disabled when local model selected
  - Info message indicating token not required for local model
  - Model dropdown now includes "local-paddleocr" option
- **Architecture Refactoring**: Reorganized code into a clean modular structure
  - Created `snip_ocr` package with focused modules:
    - `config.py`: Configuration management
    - `constants.py`: Application constants and settings
    - `updater.py`: Update checking and installation
    - `worker.py`: AI worker thread for cloud models
    - `local_worker.py`: Local OCR worker using PaddleOCR
    - `model_downloader.py`: Model download and management
    - `manager.py`: Main application manager
    - `ui/`: UI components (settings_dialog, model_dialog, snipper, update_dialog)
  - `main.py` is now a minimal entry point
  - Improved code organization and maintainability
  - Better separation of concerns

### Technical
- Added `paddleocr` and `paddlepaddle` dependencies
- Updated `pyproject.toml` to reflect new package structure
- All modules pass linting with `ruff`
- Backward compatible with existing configuration files
- PaddleOCR v3.4.0+ API compatibility

## [0.1.0] - Initial Release

### Added
- Screenshot capture with `Ctrl+Shift+S` hotkey
- AI-powered OCR using GitHub Models API
- LaTeX formula support (inline and block)
- Multi-language output (Italian/English with auto-translation)
- Model selection (GPT-4o / GPT-4o-mini)
- System tray integration
- Automatic clipboard copy
- Multi-monitor support
