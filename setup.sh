#!/bin/bash

# Wall-E Project Setup Script
# Automatically installs dependencies and sets up the local environment.

echo "🚀 Starting Wall-E Setup..."

# 1. Check & Install Homebrew (Mac Only)
if [[ "$OSTYPE" == "darwin"* ]]; then
    if ! command -v brew &> /dev/null; then
        echo "🍺 Homebrew not found. Installing..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    else
        echo "✅ Homebrew is already installed."
    fi

    # 2. Install MediaMTX (RTMP Server)
    if ! command -v mediamtx &> /dev/null; then
        echo "📡 Installing MediaMTX (RTMP Server)..."
        brew install mediamtx
    else
        echo "✅ MediaMTX is already installed."
    fi

    # 3. Start MediaMTX Service
    if ! pgrep -x "mediamtx" > /dev/null; then
        echo "▶️ Starting MediaMTX..."
        brew services start mediamtx
        sleep 2
    else
        echo "✅ MediaMTX is already running."
    fi
else
    echo "⚠️  Non-macOS detected. Please install 'mediamtx' manually."
fi

# 4. Setup Backend Python Environment
echo "🐍 Setting up Python Backend..."
cd backend || exit

# Create venv if not exists
if [ ! -d ".venv" ]; then
    echo "   Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate & Install
source .venv/bin/activate
echo "   Installing dependencies..."
pip install -r requirements.txt

echo "🎉 Setup Complete!"
echo "To run the server:"
echo "  uvicorn backend.main:app --reload"
