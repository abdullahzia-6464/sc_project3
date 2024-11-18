#!/bin/bash

# Script to instantiate 8 satellite servers starting from port 8002

START_PORT=33002
NUM_SATELLITES=5
SATELLITE_SCRIPT="src/devices/satellite.py"

# File to store PIDs of running satellites
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

# Launch satellites on consecutive ports
for ((i = 0; i < NUM_SATELLITES; i++)); do
    PORT=$((START_PORT + i))
    echo "Starting satellite on port $PORT..."
    python3 $SATELLITE_SCRIPT $PORT &
    echo $! >> "$PID_FILE"  # Save the process ID
done

echo "All satellites launched successfully!"
