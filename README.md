# Snip OCR

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Windows](https://img.shields.io/badge/Windows-0078D6?logo=windows)](https://github.com/giopalma/snip-ocr/releases)
[![macOS](https://img.shields.io/badge/macOS-000000?logo=apple)](https://github.com/giopalma/snip-ocr/releases)

**Screenshot to Markdown converter** with AI-powered OCR and full LaTeX support.

Capture any region of your screen with a hotkey, and instantly get clean Markdown in your clipboard — perfect for scientific documents, math formulas, and technical content.

## ✨ Features

- 🖼️ **Screen Region Capture** — Select any area with `Ctrl+Shift+S`
- 🔬 **Scientific OCR** — Accurate extraction of text, formulas, and tables
- 📐 **LaTeX Support** — Automatic `$...$` inline and `$$...$$` block formatting
- 🌍 **Multi-language** — Output in Italian or English (auto-translates if needed)
- 🤖 **Model Selection** — Choose between GPT-4o and GPT-4o-mini
- 📋 **Clipboard Ready** — Markdown copied instantly, ready to paste
- 🖥️ **System Tray** — Runs quietly in the background

## 🚀 Installation

### Download

Download the latest release for your platform:

| Platform    | Download                                                                                 |
| ----------- | ---------------------------------------------------------------------------------------- |
| **Windows** | [SnipOCR-Setup.exe](https://github.com/giopalma/SnipOCR/releases/tag/latest) (Installer) |
| **macOS**   | [SnipOCR-Installer.dmg](https://github.com/giopalma/SnipOCR/releases/tag/latest)         |

### First Run

On first launch, the app will ask you to configure your **GitHub Token**:

1. Go to [GitHub Personal Access Tokens](https://github.com/settings/personal-access-tokens/new)
2. Create a new token with read-only access to **Models**
3. Paste it into the Settings dialog

That's it! Your token is saved securely and you won't need to configure it again.

## 📖 Usage

1. **Start the application** — Run SnipOCR from your Start Menu or Applications folder
2. **Look for the tray icon** — The app runs in your system tray
3. **Capture a region** — Press `Ctrl+Shift+S` or click the tray icon
4. **Select the area** — Click and drag to select the screen region
5. **Paste anywhere** — The Markdown is now in your clipboard!

### Settings

Right-click the tray icon to access:

- 🌍 **Language** — Switch between Italian and English output
- 🤖 **Model** — Choose GPT-4o or GPT-4o-mini
- ⚙️ **Settings** — Update your GitHub Token

## 🛠️ Development

For contributors who want to run from source:

```bash
# Clone the repository
git clone https://github.com/giopalma/SnipOCR.git
cd SnipOCR

# Install dependencies
uv sync

# Run
uv run main.py
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for more details.

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.