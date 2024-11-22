#!/bin/bash

# Path to ship script
SHIP_SCRIPT="src/devices/ship.py"
CONFIG_FILE="src/config.py"

# Default IP address
DEFAULT_IP="127.0.0.1"

# Parse optional IP argument
IP="${1:-$DEFAULT_IP}"  # Use provided IP if available; otherwise, default to localhost

# Retrieve ship port from config.py
START_PORT=$(python3 -c "import sys; sys.path.append('$(dirname $CONFIG_FILE)'); import config; print(config.SHIP_PORT[0])")

# Check if the script exists
if [[ ! -f $SHIP_SCRIPT ]]; then
    echo "Error: $SHIP_SCRIPT not found!"
    exit 1
fi

# Run the ship server
echo "Starting Ship on $IP:$START_PORT..."
python3 $SHIP_SCRIPT --port $START_PORT --ip $IP
