#!/bin/bash

# REEL Launcher Script for macOS/Linux

echo ""
echo "========================================"
echo "   Starting REEL Music Downloader"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Python 3 is not installed!"
    echo ""
    echo "Please install Python 3.8 or higher:"
    echo "  macOS: brew install python3"
    echo "  Linux: sudo apt install python3 python3-pip"
    echo ""
    read -p "Press any key to exit..." -n 1 -s
    exit 1
fi

echo -e "${GREEN}[INFO]${NC} Python found!"
echo ""

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}[ERROR]${NC} Python $PYTHON_VERSION is too old!"
    echo "REEL requires Python 3.8 or higher"
    echo ""
    read -p "Press any key to exit..." -n 1 -s
    exit 1
fi

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}[ERROR]${NC} requirements.txt not found!"
    echo "Make sure you're running this from the REEL folder."
    echo ""
    read -p "Press any key to exit..." -n 1 -s
    exit 1
fi

# Check if reel.py exists
if [ ! -f "reel.py" ]; then
    echo -e "${RED}[ERROR]${NC} reel.py not found!"
    echo "Make sure you're running this from the REEL folder."
    echo ""
    read -p "Press any key to exit..." -n 1 -s
    exit 1
fi

# Check if required packages are installed
echo -e "${GREEN}[INFO]${NC} Checking dependencies..."

MISSING=0
python3 -c "import yt_dlp" 2>/dev/null || MISSING=1
python3 -c "import spotipy" 2>/dev/null || MISSING=1
python3 -c "import mutagen" 2>/dev/null || MISSING=1
python3 -c "import requests" 2>/dev/null || MISSING=1
python3 -c "import lyricsgenius" 2>/dev/null || MISSING=1
python3 -c "import colorama" 2>/dev/null || MISSING=1

if [ $MISSING -eq 1 ]; then
    echo -e "${YELLOW}[WARNING]${NC} Some dependencies are missing!"
    echo ""
    read -p "Would you like to install them now? [y/n]: " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo -e "${GREEN}[INFO]${NC} Installing dependencies..."
        echo ""
        pip3 install -r requirements.txt
        
        if [ $? -ne 0 ]; then
            echo ""
            echo -e "${RED}[ERROR]${NC} Failed to install dependencies!"
            echo ""
            echo "Please try manually:"
            echo "  pip3 install -r requirements.txt"
            echo ""
            read -p "Press any key to exit..." -n 1 -s
            exit 1
        fi
        
        echo ""
        echo -e "${GREEN}[SUCCESS]${NC} Dependencies installed successfully!"
        echo ""
    else
        echo ""
        echo -e "${YELLOW}[WARNING]${NC} Continuing without installing dependencies..."
        echo "REEL may not work properly!"
        echo ""
    fi
else
    echo -e "${GREEN}[SUCCESS]${NC} All dependencies are installed!"
    echo ""
fi

# Check if FFmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${YELLOW}[WARNING]${NC} FFmpeg is not installed!"
    echo "FFmpeg is required for audio conversion."
    echo ""
    echo "Install FFmpeg:"
    echo "  macOS: brew install ffmpeg"
    echo "  Linux: sudo apt install ffmpeg"
    echo ""
    read -p "Press any key to continue anyway..." -n 1 -s
    echo ""
    echo ""
else
    echo -e "${GREEN}[SUCCESS]${NC} FFmpeg found!"
    echo ""
fi

# Run REEL
echo "========================================"
echo "   Launching REEL..."
echo "========================================"
echo ""

python3 reel.py
EXIT_CODE=$?

# Always pause at the end
echo ""
echo ""
echo "========================================"
echo "   REEL has closed"
echo "========================================"
echo ""
read -p "Press any key to exit..." -n 1 -s
echo ""
