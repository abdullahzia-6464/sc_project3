#!/bin/bash

# Path to ground control script
GROUND_CONTROL_SCRIPT="src/devices/ground_control.py"
CONFIG_FILE="src/config.py"

# Default IP address
DEFAULT_IP="127.0.0.1"

# Parse optional IP argument
IP="${1:-$DEFAULT_IP}"  # Use provided IP if available; otherwise, default to localhost

# Retrieve port from config.py
GROUND_CONTROL_PORT=$(python3 -c "import sys; sys.path.append('$(dirname $CONFIG_FILE)'); import config; print(config.GROUND_CONTROL_PORT)")

# Check if the script exists
if [[ ! -f $GROUND_CONTROL_SCRIPT ]]; then
    echo "Error: $GROUND_CONTROL_SCRIPT not found!"
    exit 1
fi

# Run the ground control server
echo "Starting Ground Control on $IP:$GROUND_CONTROL_PORT..."
python3 $GROUND_CONTROL_SCRIPT --ip $IP
