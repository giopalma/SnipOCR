"""Constants and configuration for SnipOCR application."""

# Application metadata
APP_NAME = "SnipOCR"  # Used for file paths and directories
APP_DISPLAY_NAME = "Snip OCR"  # Used for UI display
GITHUB_REPO_OWNER = "giopalma"
GITHUB_REPO_NAME = "SnipOCR"

# API configuration
ENDPOINT: str = "https://models.inference.ai.azure.com/chat/completions"

# Hotkey configuration
HOTKEY_SHORTCUT = "Ctrl+Shift+S"

# Available models
AVAILABLE_MODELS = ["gpt-4o", "gpt-4o-mini"]

# Language mapping
LANGUAGE_MAP: dict[str, str] = {
    "Italiano": "Italian",
    "English": "English",
}

# System prompt template
SYSTEM_PROMPT_TEMPLATE: str = (
    "You are a scientific transcriber. "
    "Analyze the image and convert it to faithful Markdown. "
    "Preserve headings, lists, and tables. "
    "MANDATORY: use $...$ for inline LaTeX and $$...$$ for blocks. "
    "Detect the original language of the text. "
    "If the image language does NOT match the requested output language, "
    "translate accurately to the requested language. "
    "Return ONLY the Markdown content, without preambles or code blocks. "
    "Requested output language: {target_language}."
)
