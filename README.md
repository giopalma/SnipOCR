# Snip OCR

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.5+-green.svg)](https://pypi.org/project/PyQt6/)

**Screenshot to Markdown converter** with AI-powered OCR and full LaTeX support.

Capture any region of your screen with a hotkey, and instantly get clean Markdown in your clipboard — perfect for scientific documents, math formulas, and technical content.

## ✨ Features

- 🖼️ **Screen Region Capture** — Select any area with `Ctrl+Shift+S`
- 🔬 **Scientific OCR** — Accurate extraction of text, formulas, and tables
- 📐 **LaTeX Support** — Automatic `$...$` inline and `$$...$$` block formatting
- 🌍 **Multi-language** — Output in Italian or English (auto-translates if needed)
- 📋 **Clipboard Ready** — Markdown copied instantly, ready to paste
- 🖥️ **System Tray** — Runs quietly in the background

## 🚀 Installation

### Prerequisites

- Python 3.11 or higher
- A [GitHub Token](https://github.com/settings/tokens) for the Azure AI endpoint

### Using uv (recommended)

```bash
# Clone the repository
git clone https://github.com/username/snip-ocr.git
cd snip-ocr

# Install dependencies
uv sync

# Configure your token
cp .env.example .env
# Edit .env and add your GITHUB_TOKEN

# Run
uv run main.py
```

### Using pip

```bash
pip install -r requirements.txt
python main.py
```

## ⚙️ Configuration

Create a `.env` file in the project root:

```env
GITHUB_TOKEN=your_github_token_here
```

## 📖 Usage

1. **Start the application** — Run `uv run main.py`
2. **Look for the tray icon** — The app runs in your system tray
3. **Capture a region** — Press `Ctrl+Shift+S` or click the tray icon
4. **Select the area** — Click and drag to select the screen region
5. **Paste anywhere** — The Markdown is now in your clipboard!

### Changing Output Language

Right-click the tray icon to switch between:

- 🇮🇹 **Italiano**
- 🇬🇧 **English**

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.
