# OutlineCheck

OutlineCheck is a **Python-based tool** for analyzing and fixing **bad outlines in pixel art sprites**.

It detects common outline issues such as staircase effects, jaggies, and broken outlines, then applies automatic corrections to improve visual consistency and readability.

## Features

- Automatic outline analysis
- Detection of staircase outlines
- Detection of jaggies and broken outlines
- Smart outline correction
- Designed for pixel art sprites
- Useful for artists and game developers

## How It Works

OutlineCheck scans sprite contours pixel by pixel to identify outline patterns that break pixel art rules.  
Detected errors are corrected using simple and consistent outline logic.

## Goal

The goal of OutlineCheck is to **save time** and **improve sprite quality** by automating outline cleanup.

## Tech Stack

- Python 3
- Image processing libraries (PyQt6, Pillow, NumPy)

## Status

This project is currently under development.


## Requirements

Python 3.10+

NumPy

Pillow

PyQt6

# Install dependencies:
```bash
pip install numpy pillow pyqt6
git clone https://github.com/yourname/OutlineCheck.git
cd OutlineCheck
```

# Usage

1) Launch the application
2) Choose the interface language (English / Français)
3) Load a sprite file (PNG only)
4) Analyze outlines
5) Apply automatic corrections
6) Export as PNG
