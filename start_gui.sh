#!/bin/bash

# Dutch Tax Calculator - Start Script
# Starts the Flask web application

echo "🇳🇱 Starting Dutch Tax Calculator GUI..."
echo ""

# Install dependencies
python3 -m pip install -r requirements.txt --quiet

echo "Starting Flask app on http://localhost:8000"
echo "Press Ctrl+C to stop the server"
echo ""

# Start the app
python3 app.py
