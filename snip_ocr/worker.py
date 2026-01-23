"""AI worker thread for OCR processing."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

import requests
from PyQt6.QtCore import QObject, pyqtSignal

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class AIWorker(QObject):
    """Background worker for AI API calls.

    Handles the communication with the AI endpoint in a separate thread
    to prevent UI freezing during processing.

    Signals:
        finished: Emitted with the transcribed text on success.
        error: Emitted with error message on failure.
    """

    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(
        self,
        img_b64: str,
        target_language: str,
        endpoint: str,
        github_token: str,
        model_config: dict,
        system_prompt: str,
    ) -> None:
        """Initialize the AI worker.

        Args:
            img_b64: Base64-encoded PNG image data.
            target_language: Target language for transcription/translation.
            endpoint: API endpoint URL.
            github_token: GitHub authentication token.
            model_config: Model configuration dict.
            system_prompt: System prompt for the AI.
        """
        super().__init__()
        self.img_b64 = img_b64
        self.target_language = target_language
        self.endpoint = endpoint
        self.github_token = github_token
        self.model_config = model_config
        self.system_prompt = system_prompt
        self.cancelled = False

    def cancel(self) -> None:
        """Request cancellation of the current operation."""
        self.cancelled = True

    def run(self) -> None:
        """Execute the API call with retry logic."""
        retries = 3
        last_err = ""

        for i in range(retries):
            if self.cancelled:
                self.error.emit("Operation cancelled.")
                return

            try:
                headers = {
                    "Authorization": f"Bearer {self.github_token}",
                    "Content-Type": "application/json",
                }
                payload = {
                    **self.model_config,
                    "messages": [
                        {"role": "system", "content": self.system_prompt},
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": (
                                        "Transcribe accurately. "
                                        f"Output language: {self.target_language}."
                                    ),
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{self.img_b64}"
                                    },
                                },
                            ],
                        },
                    ],
                }

                response = requests.post(
                    self.endpoint, json=payload, headers=headers, timeout=45
                )
                response.raise_for_status()

                data = response.json()
                choices = data.get("choices", [])
                if (
                    choices
                    and "message" in choices[0]
                    and "content" in choices[0]["message"]
                ):
                    content = choices[0]["message"]["content"]
                    self.finished.emit(content.strip())
                    return
                raise ValueError("Invalid JSON response format")

            except Exception as e:
                last_err = str(e)
                logger.warning("Attempt %d failed: %s", i + 1, last_err)
                time.sleep(1.5)

        self.error.emit(f"Failed after {retries} attempts. Last error: {last_err}")
