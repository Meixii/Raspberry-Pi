#!/bin/bash

# Start the backend server in the background using virtual environment
source ../venv/bin/activate
python main.py &

# Wait a few seconds for the server to start
sleep 3

# Deactivate virtual environment before running GUI
deactivate

# Start the GUI application using system Python
python3 gui.py

# When GUI is closed, kill the backend server
pkill -f "python main.py" 