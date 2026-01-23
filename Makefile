# Makefile for Snip OCR

# Variables
PYINSTALLER_SPEC = snip_ocr.spec
INNO_SETUP_DIR = "C:\Program Files (x86)\Inno Setup 6"
ISCC = $(INNO_SETUP_DIR)\ISCC.exe

.PHONY: help run build clean installer

help:
	@echo "Available commands:"
	@echo "  make run        - Run the application using uv"
	@echo "  make build      - Build the standalone executable using PyInstaller"
	@echo "  make clean      - Remove build and dist directories"
	@echo "  make installer  - Build the Inno Setup installer (requires Inno Setup)"

run:
	uv run main.py

build:
	uv run pyinstaller $(PYINSTALLER_SPEC) --distpath dist --workpath build --noconfirm

clean:
	@if exist build rmdir /s /q build
	@if exist dist rmdir /s /q dist

installer: build
	@if exist $(ISCC) ( \
		$(ISCC) "installer.iss" \
	) else ( \
		echo "Error: Inno Setup (ISCC.exe) not found."; \
		echo "Please check the path in the Makefile."; \
	)
