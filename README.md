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
- 🤖 **Model Selection** — Choose between GPT-4o, GPT-4o-mini, or local PaddleOCR
- 🔌 **Offline Mode** — Use local PaddleOCR model without internet connection
- 📋 **Clipboard Ready** — Markdown copied instantly, ready to paste
- 🖥️ **System Tray** — Runs quietly in the background
- 🔄 **Auto-Update** — Automatic update notifications and one-click updates

## 🚀 Installation

### Download

Download the latest release for your platform:

| Platform    | Download                                                                                 |
| ----------- | ---------------------------------------------------------------------------------------- |
| **Windows** | [SnipOCR-Setup.exe](https://github.com/giopalma/SnipOCR/releases/tag/latest) (Installer) |
| **macOS**   | [SnipOCR-Installer.dmg](https://github.com/giopalma/SnipOCR/releases/tag/latest)         |

### First Run

#### Using Cloud Models (GPT-4o/GPT-4o-mini)

On first launch with cloud models, the app will ask you to configure your **GitHub Token**:

1. Go to [GitHub Personal Access Tokens](https://github.com/settings/personal-access-tokens/new)
2. Create a new token with read-only access to **Models**
3. Paste it into the Settings dialog

That's it! Your token is saved securely and you won't need to configure it again.

#### Using Local Model (PaddleOCR)

To use the offline local model:

1. Right-click the system tray icon → **Settings**
2. Select **local-paddleocr** from the Model dropdown
3. No GitHub Token required!
4. Right-click the system tray icon → **Manage Models**
5. Click **Download Models** to initialize (~150 MB download)

Once downloaded, you can use SnipOCR completely offline.

## 📖 Usage

1. **Start the application** — Run SnipOCR from your Start Menu or Applications folder
2. **Look for the tray icon** — The app runs in your system tray
3. **Capture a region** — Press `Ctrl+Shift+S` or click the tray icon
4. **Select the area** — Click and drag to select the screen region
5. **Paste anywhere** — The Markdown is now in your clipboard!

### Settings

Right-click the tray icon to access:

- 🌍 **Language** — Switch between Italian and English output
- 🤖 **Model** — Choose GPT-4o, GPT-4o-mini, or local-paddleocr
- 🔌 **Manage Models** — Download/manage local OCR models
- ⚙️ **Settings** — Update your GitHub Token (not required for local model)

### Offline Mode

The **local-paddleocr** model enables completely offline operation:

- ✅ **No internet required** after initial model download
- ✅ **No API key needed** — works without GitHub Token
- ✅ **Privacy-focused** — all processing happens locally
- ✅ **Hardware acceleration** — supports CPU, CUDA GPU, and Intel ARC (XPU)
- ⚠️ **Initial setup** — requires ~150 MB download on first use

**Note:** The local model is optimized for text recognition. For complex mathematical formulas and advanced layout analysis, cloud models (GPT-4o) may provide better results.

### Updates

The app automatically checks for updates on startup. When a new version is available:
- You'll receive a notification that you can click to download
- An "Update Available" option appears in the system tray menu
- Updates are downloaded and installed with a single click
- You can choose to install immediately or continue using the current version

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

For information about the project architecture, see [ARCHITECTURE.md](ARCHITECTURE.md).

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.