#!/bin/bash

# Solana Copy Trading Bot Runner Script

echo "=================================="
echo "Solana Copy Trading Bot"
echo "=================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "venv/installed" ]; then
    echo "Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    touch venv/installed
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found!"
    echo "Please copy .env.example to .env and configure it:"
    echo "  cp .env.example .env"
    echo "  nano .env"
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p logs

echo ""
echo "Starting bot..."
echo "Press Ctrl+C to stop"
echo ""

# Run the bot
python -m python_bot.main

# Deactivate virtual environment on exit
deactivate
