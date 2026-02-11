# Fix Issues Memory - Settings Dialog Refactoring

## Issues Identified

### 1. AttributeError in settings_dialog.py (CRITICAL)
**Problem**: Line 99 tries to access `self.info_label` causing AttributeError
**Solution**: info_label exists at line 72, need to verify exact issue

### 2. Model Download Progress Issue  
**Problem**: Progress stays at 10% then shows "Download Failed"
**Solution**: Fix progress reporting in model_downloader.py

### 3. Dark Theme Visibility
**Problem**: Blue text not visible in dark theme
**Solution**: Use palette-based colors

### 4. UI Reorganization
**Problem**: Need to consolidate model download and updates into Settings
**Solution**: Create tabbed settings dialog with all functionality

## Implementation Phases

1. Fix critical AttributeError bug
2. Fix progress and theme issues
3. Refactor settings dialog with tabs
4. Test and validate
