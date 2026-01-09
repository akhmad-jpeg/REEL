@echo off
title REEL - Music Downloader
color 0A

echo.
echo ========================================
echo    Starting REEL Music Downloader
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo.
    echo Please install Python 3.8 or higher from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [INFO] Python found!
echo.

REM Check if requirements.txt exists
if not exist requirements.txt (
    echo [ERROR] requirements.txt not found!
    echo Make sure you're running this from the REEL folder.
    echo.
    pause
    exit /b 1
)

REM Check if reel.py exists
if not exist reel.py (
    echo [ERROR] reel.py not found!
    echo Make sure you're running this from the REEL folder.
    echo.
    pause
    exit /b 1
)

REM Try to import dependencies
echo [INFO] Checking dependencies...
python -c "import yt_dlp" >nul 2>&1
if errorlevel 1 goto missing_deps

python -c "import spotipy" >nul 2>&1
if errorlevel 1 goto missing_deps

python -c "import mutagen" >nul 2>&1
if errorlevel 1 goto missing_deps

python -c "import requests" >nul 2>&1
if errorlevel 1 goto missing_deps

python -c "import lyricsgenius" >nul 2>&1
if errorlevel 1 goto missing_deps

python -c "import colorama" >nul 2>&1
if errorlevel 1 goto missing_deps

echo [SUCCESS] All dependencies are installed!
echo.
goto check_ffmpeg

:missing_deps
echo [WARNING] Some dependencies are missing!
echo.
set /p install_deps="Would you like to install them now? [Y/N]: "
if /i "%install_deps%"=="Y" (
    echo.
    echo [INFO] Installing dependencies...
    echo.
    pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [ERROR] Failed to install dependencies!
        echo.
        echo Please try manually:
        echo   pip install -r requirements.txt
        echo.
        pause
        exit /b 1
    )
    echo.
    echo [SUCCESS] Dependencies installed successfully!
    echo.
) else (
    echo.
    echo [WARNING] Continuing without installing dependencies...
    echo REEL may not work properly!
    echo.
)

:check_ffmpeg
REM Check if FFmpeg is installed
where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo [WARNING] FFmpeg is not installed or not in PATH!
    echo FFmpeg is required for audio conversion.
    echo.
    echo Install FFmpeg:
    echo   - Windows: choco install ffmpeg
    echo   - Or download from: https://www.gyan.dev/ffmpeg/builds/
    echo.
    echo Press any key to continue anyway...
    pause >nul
    echo.
) else (
    echo [SUCCESS] FFmpeg found!
    echo.
)

REM Run REEL
echo ========================================
echo    Launching REEL...
echo ========================================
echo.
python reel.py

REM Always pause at the end
echo.
echo.
echo ========================================
echo    REEL has closed
echo ========================================
echo.
pause
