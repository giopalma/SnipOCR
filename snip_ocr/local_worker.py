"""Local OCR worker using PaddleOCR for offline processing."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from PyQt6.QtCore import QObject, pyqtSignal

from .model_downloader import get_models_path

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
            Tuple of (ocr_engine, structure_engine) or raises exception.
        """
        from paddleocr import PaddleOCR, PPStructure
        
        models_path = get_models_path()
        hardware = self._detect_hardware()
        
        # Set environment variable for PaddlePaddle
        if hardware == "xpu":
            os.environ["FLAGS_use_xpu"] = "1"
        
        use_gpu = hardware in ("gpu", "xpu")
        
        # Configure OCR engine
        ocr_kwargs = {
            "use_angle_cls": True,
            "lang": "en",  # English models work well for multilingual content
            "use_gpu": use_gpu,
            "show_log": False,
            "det_model_dir": str(models_path / "det"),
            "rec_model_dir": str(models_path / "rec"),
            "cls_model_dir": str(models_path / "cls"),
        }
        
        # Configure structure analysis engine (for tables)
        structure_kwargs = {
            "use_gpu": use_gpu,
            "show_log": False,
            "table_model_dir": str(models_path / "structure"),
        }
        
        try:
            ocr = PaddleOCR(**ocr_kwargs)
            structure = PPStructure(**structure_kwargs)
            return ocr, structure
        except Exception as e:
            logger.error(f"Failed to initialize PaddleOCR: {e}")
            raise

    def _convert_to_markdown(self, ocr_result: list, structure_result: list) -> str:
        """Convert OCR and structure results to Markdown format.

        Args:
            ocr_result: Text detection and recognition results.
            structure_result: Table and layout analysis results.

        Returns:
            Formatted Markdown string with LaTeX for formulas.
        """
        markdown_lines = []
        
        # Process structure results first (tables, etc.)
        if structure_result:
            for item in structure_result:
                if item.get("type") == "table":
                    # Extract table HTML and convert to markdown
                    table_html = item.get("res", {}).get("html", "")
                    if table_html:
                        markdown_lines.append(self._html_table_to_markdown(table_html))
                        markdown_lines.append("")
        
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

    def _html_table_to_markdown(self, html: str) -> str:
        """Convert HTML table to Markdown table format.

        Args:
            html: HTML table string.

        Returns:
            Markdown table string.
        """
        # Basic HTML to Markdown table conversion
        # This is a simplified version; for production, consider using a library
        try:
            from html.parser import HTMLParser
            
            class TableParser(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.rows = []
                    self.current_row = []
                    self.current_cell = []
                    self.in_table = False
                    
                def handle_starttag(self, tag, attrs):
                    if tag == "table":
                        self.in_table = True
                    elif tag == "tr":
                        self.current_row = []
                    elif tag in ("td", "th"):
                        self.current_cell = []
                
                def handle_endtag(self, tag):
                    if tag == "table":
                        self.in_table = False
                    elif tag == "tr":
                        if self.current_row:
                            self.rows.append(self.current_row)
                    elif tag in ("td", "th"):
                        self.current_row.append("".join(self.current_cell).strip())
                
                def handle_data(self, data):
                    if self.in_table:
                        self.current_cell.append(data)
            
            parser = TableParser()
            parser.feed(html)
            
            if not parser.rows:
                return ""
            
            # Build markdown table
            md_lines = []
            for i, row in enumerate(parser.rows):
                md_lines.append("| " + " | ".join(row) + " |")
                if i == 0:  # Add header separator
                    md_lines.append("| " + " | ".join(["---"] * len(row)) + " |")
            
            return "\n".join(md_lines)
            
        except Exception as e:
            logger.warning(f"Failed to convert HTML table: {e}")
            return html

    def run(self) -> None:
        """Execute the local OCR processing."""
        try:
            if self.cancelled:
                self.error.emit("Operation cancelled.")
                return
            
            # Initialize PaddleOCR
            logger.info("Initializing PaddleOCR engines")
            ocr, structure = self._initialize_paddleocr()
            
            if self.cancelled:
                self.error.emit("Operation cancelled.")
                return
            
            # Perform OCR
            logger.info(f"Processing image: {self.image_path}")
            ocr_result = ocr.ocr(self.image_path, cls=True)
            
            if self.cancelled:
                self.error.emit("Operation cancelled.")
                return
            
            # Perform structure analysis (tables, layout)
            logger.info("Analyzing document structure")
            structure_result = structure(self.image_path)
            
            if self.cancelled:
                self.error.emit("Operation cancelled.")
                return
            
            # Convert to Markdown
            logger.info("Converting to Markdown")
            markdown_text = self._convert_to_markdown(
                ocr_result[0] if ocr_result else [],
                structure_result
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
