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

# Output formats
OUTPUT_FORMATS = ["Markdown", "Word/Google Docs"]
DEFAULT_OUTPUT_FORMAT = OUTPUT_FORMATS[0]

# Language mapping
LANGUAGE_MAP: dict[str, str] = {
    "Italiano": "Italian",
    "English": "English",
}

# System prompt templates
SYSTEM_PROMPT_TEMPLATES: dict[str, str] = {
    "Markdown": (
        "You are a scientific transcriber. "
        "Analyze the image and convert it to faithful Markdown. "
        "Preserve headings, lists, and tables. "
        "MANDATORY: use $...$ for inline LaTeX and $$...$$ for blocks. "
        "Detect the original language of the text. "
        "If the image language does NOT match the requested output language, "
        "translate accurately to the requested language. "
        "Return ONLY the Markdown content, without preambles or code blocks. "
        "Requested output language: {target_language}."
    ),
    "Word/Google Docs": (
        "You are a scientific transcriber. "
        "Analyze the image and convert it to HTML optimized for Microsoft Word "
        "and Google Docs paste. "
        "Preserve headings, lists, and tables with inline CSS similar to "
        "Google Docs. Output should start with <meta charset=\"utf-8\"> and "
        "wrap all content in <b style=\"font-weight:normal;\" "
        "id=\"docs-internal-guid-UNIQUE\"><div dir=\"ltr\" align=\"left\">. "
        "Use <table style=\"border:none;border-collapse:collapse;\"> with "
        "colgroup widths and cell styles like "
        "border-left/right/top/bottom and padding. "
        "MANDATORY: render formulas as inline <img> tags with "
        "data:image/svg+xml;utf8,... and set style="
        "\"vertical-align:middle;\" so Google Docs shows them as images "
        "(do NOT use MathML). "
        "Detect the original language of the text. "
        "If the image language does NOT match the requested output language, "
        "translate accurately to the requested language. "
        "Return ONLY the HTML fragment, without preambles or code blocks. "
        "Requested output language: {target_language}."
    ),
}
