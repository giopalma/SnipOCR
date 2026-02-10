"""Model downloader for local OCR models."""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

from .config import get_config_path

logger = logging.getLogger(__name__)


def get_models_path() -> Path:
    """Get the path to the models directory.

    Returns:
        Path to models directory in app config folder.
    """
    models_dir = get_config_path() / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    return models_dir


def is_model_downloaded() -> bool:
    """Check if PaddleOCR models are already downloaded.

    Returns:
        True if models exist, False otherwise.
    """
    # PaddleOCR auto-downloads models to its cache directory
    # We check if the default models have been initialized
    models_path = get_models_path()
    marker_file = models_path / ".models_ready"
    return marker_file.exists()


def download_models(
    progress_callback: Callable[[int, int], None] | None = None
) -> bool:
    """Download PaddleOCR models.

    This initializes PaddleOCR which will auto-download the necessary models
    to its cache directory on first use.

    Args:
        progress_callback: Optional callback function(current, total) for progress.

    Returns:
        True if download successful, False otherwise.
    """
    models_path = get_models_path()
    
    try:
        from paddleocr import PaddleOCR
        
        logger.info("Initializing PaddleOCR - models will be auto-downloaded")
        
        if progress_callback:
            progress_callback(10, 100)
        
        # Initialize PaddleOCR - this will trigger model download
        ocr = PaddleOCR(
            lang="en",
            use_textline_orientation=True,
            ocr_version="PP-OCRv4",
        )
        
        if progress_callback:
            progress_callback(50, 100)
        
        # Test with a small dummy image to ensure models are loaded
        import numpy as np
        dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
        _ = ocr(dummy_img)
        
        if progress_callback:
            progress_callback(90, 100)
        
        # Create marker file to indicate models are ready
        marker_file = models_path / ".models_ready"
        marker_file.write_text("ready")
        
        if progress_callback:
            progress_callback(100, 100)
        
        logger.info("Models downloaded and verified successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to download models: {e}")
        return False


def delete_models() -> bool:
    """Delete downloaded models marker to allow re-download.

    Returns:
        True if deletion successful, False otherwise.
    """
    try:
        models_path = get_models_path()
        marker_file = models_path / ".models_ready"
        if marker_file.exists():
            marker_file.unlink()
        return True
    except Exception as e:
        logger.error(f"Failed to delete models marker: {e}")
        return False


def get_model_size() -> int:
    """Get the approximate size of PaddleOCR cache.

    Returns:
        Estimated size in bytes.
    """
    if not is_model_downloaded():
        return 0
    
    # PaddleOCR stores models in its own cache directory
    # We return an approximate size
    return 150 * 1024 * 1024  # ~150 MB estimate


def format_size(size_bytes: int) -> str:
    """Format size in bytes to human-readable string.

    Args:
        size_bytes: Size in bytes.

    Returns:
        Formatted string like "1.5 MB".
    """
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"
