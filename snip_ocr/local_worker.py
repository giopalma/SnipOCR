"""Local OCR worker using PaddleOCR for offline processing."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from PyQt6.QtCore import QObject, pyqtSignal

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class LocalOCRWorker(QObject):
    """Background worker for local OCR processing using PaddleOCR.

    Handles OCR processing locally without requiring API calls.
    Supports text, mathematical formulas, tables, and structured content.

    Signals:
        finished: Emitted with the transcribed text on success.
        error: Emitted with error message on failure.
    """

    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(
        self,
        image_path: str,
        target_language: str,
    ) -> None:
        """Initialize the local OCR worker.

        Args:
            image_path: Path to the image file to process.
            target_language: Target language for output (Italian/English).
        """
        super().__init__()
        self.image_path = image_path
        self.target_language = target_language
        self.cancelled = False

    def cancel(self) -> None:
        """Request cancellation of the current operation."""
        self.cancelled = True

    def _detect_hardware(self) -> str:
        """Detect available hardware acceleration.

        Returns:
            "gpu" for CUDA, "xpu" for Intel ARC, "cpu" for CPU only.
        """
        try:
            import paddle
            
            # Check for XPU (Intel ARC)
            if paddle.device.is_compiled_with_xpu():
                xpu_count = paddle.device.xpu.device_count()
                if xpu_count > 0:
                    logger.info(f"XPU detected: {xpu_count} device(s)")
                    return "xpu"
            
            # Check for CUDA GPU
            if paddle.device.is_compiled_with_cuda():
                gpu_count = paddle.device.cuda.device_count()
                if gpu_count > 0:
                    logger.info(f"CUDA GPU detected: {gpu_count} device(s)")
                    return "gpu"
            
            logger.info("No GPU detected, using CPU")
            return "cpu"
            
        except Exception as e:
            logger.warning(f"Hardware detection failed: {e}, defaulting to CPU")
            return "cpu"

    def _initialize_paddleocr(self):
        """Initialize PaddleOCR with appropriate hardware backend.

        Returns:
            PaddleOCR engine instance.
        """
        from paddleocr import PaddleOCR
        
        hardware = self._detect_hardware()
        
        # Set environment variable for PaddlePaddle
        if hardware == "xpu":
            os.environ["FLAGS_USE_XPU"] = "1"
        elif hardware == "gpu":
            os.environ["FLAGS_USE_CUDA"] = "1"
        
        # Configure OCR engine with new API
        ocr_kwargs = {
            "lang": "en",  # English models work well for multilingual content
            "use_textline_orientation": True,  # Enable angle correction
            "ocr_version": "PP-OCRv4",  # Use latest version
        }
        
        try:
            ocr = PaddleOCR(**ocr_kwargs)
            return ocr
        except Exception as e:
            logger.error(f"Failed to initialize PaddleOCR: {e}")
            raise

    def _convert_to_markdown(self, ocr_result: list) -> str:
        """Convert OCR results to Markdown format.

        Args:
            ocr_result: Text detection and recognition results.

        Returns:
            Formatted Markdown string with LaTeX for formulas.
        """
        markdown_lines = []
        
        # Process OCR text results
        if ocr_result:
            for line in ocr_result:
                if len(line) >= 2:
                    # line[0] contains bbox, line[1] contains (text, confidence)
                    text = line[1][0] if isinstance(line[1], (list, tuple)) else line[1]
                    
                    # Detect and format mathematical formulas
                    if self._contains_math(text):
                        text = self._format_math(text)
                    
                    markdown_lines.append(text)
        
        result = "\n".join(markdown_lines).strip()
        
        # Post-process: clean up excessive newlines
        while "\n\n\n" in result:
            result = result.replace("\n\n\n", "\n\n")
        
        return result

    def _contains_math(self, text: str) -> bool:
        """Detect if text likely contains mathematical notation.

        Args:
            text: Text to check.

        Returns:
            True if text appears to contain math symbols.
        """
        math_indicators = [
            "=", "+", "-", "×", "÷", "±", "≠", "≈", "≤", "≥",
            "∫", "∑", "∏", "√", "∞", "π", "α", "β", "γ", "θ",
            "λ", "μ", "σ", "Δ", "∂", "∇"
        ]
        return any(indicator in text for indicator in math_indicators)

    def _format_math(self, text: str) -> str:
        """Format mathematical expressions with LaTeX delimiters.

        Args:
            text: Text potentially containing math.

        Returns:
            Text with LaTeX formatting applied.
        """
        # Simple heuristic: if line looks like an equation, wrap in $$
        if "=" in text and len(text.strip()) < 100:
            return f"$${text.strip()}$$"
        else:
            # Inline math for shorter expressions
            return f"${text.strip()}$"

    def run(self) -> None:
        """Execute the local OCR processing."""
        try:
            if self.cancelled:
                self.error.emit("Operation cancelled.")
                return
            
            # Initialize PaddleOCR
            logger.info("Initializing PaddleOCR engine")
            ocr = self._initialize_paddleocr()
            
            if self.cancelled:
                self.error.emit("Operation cancelled.")
                return
            
            # Perform OCR
            logger.info(f"Processing image: {self.image_path}")
            ocr_result = ocr(self.image_path)
            
            if self.cancelled:
                self.error.emit("Operation cancelled.")
                return
            
            # Convert to Markdown
            logger.info("Converting to Markdown")
            markdown_text = self._convert_to_markdown(
                ocr_result[0] if ocr_result else []
            )
            
            if not markdown_text:
                self.error.emit("No text detected in image.")
                return
            
            self.finished.emit(markdown_text)
            logger.info("Local OCR processing completed successfully")
            
        except Exception as e:
            error_msg = f"Local OCR failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.error.emit(error_msg)
