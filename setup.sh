#!/bin/bash

# DNSE Insight Trading Bot - Setup Script
# This script automates the installation and setup process

set -e

echo "========================================="
echo "DNSE Insight Trading Bot - Setup"
echo "========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

required_version="3.9"
if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python 3.9+ is required"
    exit 1
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Virtual environment created"
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Check if TA-Lib is installed
echo ""
echo "Checking TA-Lib installation..."
if python -c "import talib" 2>/dev/null; then
    echo "✓ TA-Lib is installed"
else
    echo "⚠ TA-Lib is not installed"
    echo ""
    echo "Please install TA-Lib manually:"
    echo ""
    echo "Ubuntu/Debian:"
    echo "  wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz"
    echo "  tar -xzf ta-lib-0.4.0-src.tar.gz"
    echo "  cd ta-lib/"
    echo "  ./configure --prefix=/usr"
    echo "  make"
    echo "  sudo make install"
    echo ""
    echo "macOS:"
    echo "  brew install ta-lib"
    echo ""
fi

# Create .env file if not exists
echo ""
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env file created"
    echo "⚠ Please edit .env file with your DNSE credentials"
else
    echo ".env file already exists"
fi

# Create necessary directories
echo ""
echo "Creating directories..."
mkdir -p logs data tests

# Set permissions
echo ""
echo "Setting permissions..."
chmod +x main.py

echo ""
echo "========================================="
echo "Setup completed successfully!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your DNSE API credentials"
echo "2. Configure Telegram bot (optional)"
echo "3. Run in paper trading mode: python main.py --symbols VCB VHM"
echo "4. Check logs in logs/ directory"
echo ""
echo "For more information, see README.md"
echo ""
