"""Model downloader for local OCR models."""

from __future__ import annotations

import logging
import os
import tarfile
from pathlib import Path
from typing import Callable

import requests

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
    models_path = get_models_path()
    # Check for essential model files
    det_model = models_path / "det" / "inference.pdmodel"
    rec_model = models_path / "rec" / "inference.pdmodel"
    cls_model = models_path / "cls" / "inference.pdmodel"
    
    return det_model.exists() and rec_model.exists() and cls_model.exists()


def download_models(
    progress_callback: Callable[[int, int], None] | None = None
) -> bool:
    """Download PaddleOCR models.

    This downloads the official PaddleOCR v4 models for:
    - Text detection
    - Text recognition
    - Angle classification
    - Structure analysis (tables)

    Args:
        progress_callback: Optional callback function(current, total) for progress.

    Returns:
        True if download successful, False otherwise.
    """
    models_path = get_models_path()
    
    # Model URLs for PaddleOCR v4
    models_to_download = {
        "det": "https://paddleocr.bj.bcebos.com/PP-OCRv4/chinese/ch_PP-OCRv4_det_infer.tar",
        "rec": "https://paddleocr.bj.bcebos.com/PP-OCRv4/chinese/ch_PP-OCRv4_rec_infer.tar",
        "cls": "https://paddleocr.bj.bcebos.com/dygraph_v2.0/ch/ch_ppocr_mobile_v2.0_cls_infer.tar",
        "structure": "https://paddleocr.bj.bcebos.com/ppstructure/models/slanet/ch_ppstructure_mobile_v2.0_SLANet_infer.tar",
    }
    
    try:
        total_models = len(models_to_download)
        
        for idx, (model_name, url) in enumerate(models_to_download.items()):
            logger.info(f"Downloading {model_name} model from {url}")
            
            # Download the tar file
            tar_path = models_path / f"{model_name}.tar"
            
            response = requests.get(url, stream=True, timeout=300)
            response.raise_for_status()
            
            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0
            
            with open(tar_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size > 0:
                            # Report overall progress
                            overall_progress = (idx * 100 + (downloaded * 100) // total_size) // total_models
                            progress_callback(overall_progress, 100)
            
            # Extract the tar file
            logger.info(f"Extracting {model_name} model")
            model_dir = models_path / model_name
            model_dir.mkdir(parents=True, exist_ok=True)
            
            with tarfile.open(tar_path, "r") as tar:
                # Extract to model_dir and handle nested structure
                tar.extractall(path=models_path)
                
                # Find the extracted directory (usually has _infer suffix)
                extracted_dirs = [d for d in models_path.iterdir() if d.is_dir() and model_name in d.name.lower()]
                if extracted_dirs:
                    # Move contents to model_dir
                    extracted_dir = extracted_dirs[0]
                    for item in extracted_dir.iterdir():
                        item.rename(model_dir / item.name)
                    extracted_dir.rmdir()
            
            # Clean up tar file
            tar_path.unlink()
            
            if progress_callback:
                progress_callback(((idx + 1) * 100) // total_models, 100)
        
        logger.info("All models downloaded successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to download models: {e}")
        return False


def delete_models() -> bool:
    """Delete downloaded models to free up space.

    Returns:
        True if deletion successful, False otherwise.
    """
    try:
        models_path = get_models_path()
        if models_path.exists():
            import shutil
            shutil.rmtree(models_path)
            models_path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Failed to delete models: {e}")
        return False


def get_model_size() -> int:
    """Get the total size of downloaded models in bytes.

    Returns:
        Size in bytes, 0 if models not downloaded.
    """
    if not is_model_downloaded():
        return 0
    
    models_path = get_models_path()
    total_size = 0
    
    for dirpath, dirnames, filenames in os.walk(models_path):
        for filename in filenames:
            filepath = Path(dirpath) / filename
            total_size += filepath.stat().st_size
    
    return total_size


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
