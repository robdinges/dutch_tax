#!/bin/bash

# Dutch Tax Calculator - Start Script
# Starts the Flask web application

echo "🇳🇱 Starting Dutch Tax Calculator GUI..."
echo ""

# Check if Flask is installed
python3 -m pip list | grep -q Flask
if [ $? -ne 0 ]; then
    echo "Installing Flask..."
    python3 -m pip install flask --quiet
fi

echo "Starting Flask app on http://localhost:5000"
echo "Press Ctrl+C to stop the server"
echo ""

# Start the app
python3 app.py
