#!/bin/bash

# Script to instantiate multiple satellite servers, storing PIDs and ports.

# Python script and config file locations
SATELLITE_SCRIPT="src/devices/satellite.py"
CONFIG_FILE="src/config.py"

# File to store PIDs and ports of running satellites
PID_FILE="satellite_pids.txt"

# Remove the PID file if it exists
if [ -f "$PID_FILE" ]; then
    rm "$PID_FILE"
fi

# Check if the satellite script exists
if [[ ! -f $SATELLITE_SCRIPT ]]; then
    echo "Error: $SATELLITE_SCRIPT not found!"
    exit 1
fi

# Read configuration from config.py
START_PORT=$(python3 -c "import sys; sys.path.append('$(dirname $CONFIG_FILE)'); import config; print(config.START_PORT)")
NUM_SATELLITES=$(python3 -c "import sys; sys.path.append('$(dirname $CONFIG_FILE)'); import config; print(config.NUM_SATELLITES)")
SATELLITE_IP=$(python3 -c "import sys; sys.path.append('$(dirname $CONFIG_FILE)'); import config; print(config.SATELLITE_IP)")

# Launch satellites on consecutive ports
for ((i = 0; i < NUM_SATELLITES; i++)); do
    PORT=$((START_PORT + i))
    echo "Starting satellite on $SATELLITE_IP:$PORT..."
    python3 $SATELLITE_SCRIPT --ip $SATELLITE_IP --port $PORT &
    PID=$!
    echo "$PID $PORT" >> "$PID_FILE"  # Save PID and port to the file
done

echo "All satellites launched successfully!"
