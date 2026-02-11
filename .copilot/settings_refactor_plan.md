# Settings Dialog Refactoring Plan

## New Structure

### Tabbed Settings Dialog
**Tab 1: OCR Model**
- Model selection dropdown (gpt-4o, gpt-4o-mini, local-paddleocr)
- GitHub Token input (disabled when local model selected)
- Info label about token requirement
- For local model: Download/status section integrated

**Tab 2: Updates**
- Check for updates button
- Current version display
- Available version display (if update found)
- Download and install button (if update available)
- Progress bar for download

**Tab 3: General**
- Language selection (Italian/English) - moved from menu
- Other app settings as needed

## Components to Reuse
- ModelDownloadWorker from model_dialog.py
- UpdateDownloader from update_dialog.py
- Model downloader functions from model_downloader.py
- Update checker from updater.py

## Changes to manager.py
- Remove "Manage Models" menu action
- Remove "Update Available" menu action (or keep as quick shortcut)
- Language selection stays in menu (quick access)
- Settings menu opens new tabbed dialog

## Files to Modify
1. settings_dialog.py - Complete rewrite with tabs
2. manager.py - Update menu and dialog calls
3. Keep model_dialog.py and update_dialog.py for reference (can deprecate later)
