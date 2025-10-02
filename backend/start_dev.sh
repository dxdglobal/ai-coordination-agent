#!/bin/bash
# AI Coordination Agent - Development Startup Script

echo "🚀 Starting AI Coordination Agent Development Environment"
echo "=================================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Initialize database if needed
if [ ! -f "database_initialized.flag" ]; then
    echo "🗄️ Initializing database..."
    python3 database/init_db.py
    touch database_initialized.flag
fi

# Start the AI Coordination Agent
echo "🤖 Starting AI Coordination Agent..."
python3 main.py