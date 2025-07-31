#!/bin/bash

echo "Starting Information Asymmetry Simulation Dashboard..."
echo "----------------------------------------"
echo "Dashboard will be available at: http://localhost:5000"
echo "Press Ctrl+C to stop the server"
echo "----------------------------------------"

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Install requirements if needed
echo "Checking dependencies..."
pip install -q -r requirements.txt

# Start the Flask app
python app.py