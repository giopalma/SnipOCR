# Contributing to Snip OCR

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Development Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/username/snip-ocr.git
   cd snip-ocr
   ```

2. **Install dependencies** (using [uv](https://github.com/astral-sh/uv))

   ```bash
   uv sync
   ```

3. **Set up environment variables**

   ```bash
   cp .env.example .env
   # Edit .env and add your GITHUB_TOKEN
   ```

4. **Run the application**
   ```bash
   uv run main.py
   ```

## Code Style

This project uses:

- **[Ruff](https://github.com/astral-sh/ruff)** for linting and formatting
- **Type hints** throughout the codebase
- **Docstrings** for all public classes and functions

Before submitting a PR, ensure your code passes:

```bash
ruff check .
ruff format .
```

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Reporting Issues

When reporting issues, please include:

- OS and Python version
- Steps to reproduce
- Expected vs actual behavior
- Any relevant error messages

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
