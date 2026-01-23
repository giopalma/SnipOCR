# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Automatic Update System**: Application now checks for updates on startup via GitHub Releases
  - Clickable notification when updates are available
  - Progress dialog showing download and installation status
  - "Update Available" menu item in system tray (visible only when updates are available)
  - Support for Windows (.exe, .msi) and macOS (.dmg) installers

### Changed
- **Architecture Refactoring**: Reorganized code into a clean modular structure
  - Created `snip_ocr` package with focused modules:
    - `config.py`: Configuration management
    - `constants.py`: Application constants and settings
    - `updater.py`: Update checking and installation
    - `worker.py`: AI worker thread
    - `manager.py`: Main application manager
    - `ui/`: UI components (settings_dialog, snipper, update_dialog)
  - `main.py` is now a minimal entry point
  - Improved code organization and maintainability
  - Better separation of concerns

### Technical
- Updated `pyproject.toml` to reflect new package structure
- All modules pass linting with `ruff`
- Backward compatible with existing configuration files

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
