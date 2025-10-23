#!/bin/bash

echo "🚀 Starting Smart RAG Web UI..."
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.13.3 or higher"
    exit 1
fi

# Make the script executable
chmod +x "$0"

# Start the web server
python3 server.py --port 8080
