@echo off
setlocal

echo 🚀 Starting Wall-E Setup for Windows...
echo.

:: 1. Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH.
    echo Please install Python 3.10+ and try again.
    pause
    exit /b 1
)

:: 2. MediaMTX Setup Instruction
echo 📡 [Step 1] MediaMTX (RTMP Server) Setup
echo    Windows does not have a package manager like Homebrew by default.
echo    Please follow these steps manually:
echo.
echo    1. Download MediaMTX from: https://github.com/bluenviron/mediamtx/releases
echo       (Look for 'mediamtx_vX.X.X_windows_amd64.zip')
echo    2. Extract the zip file.
echo    3. Run 'mediamtx.exe'.
echo.
pause

:: 3. Setup Backend Python Environment
echo.
echo 🐍 [Step 2] Setting up Python Backend...
cd backend

if not exist ".venv" (
    echo    Creating virtual environment...
    python -m venv .venv
)

echo    Installing dependencies...
call .venv\Scripts\activate.bat
pip install -r requirements.txt

echo.
echo 🎉 Setup Complete!
echo.
echo To run the server:
echo    cd backend
echo    .venv\Scripts\activate
echo    uvicorn main:app --reload
echo.
pause
