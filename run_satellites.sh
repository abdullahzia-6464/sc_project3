#!/bin/bash

# Script to instantiate multiple satellite servers, storing PIDs and ports.

# Python script and config file locations
SATELLITE_SCRIPT="src/devices/satellite.py"
CONFIG_FILE="src/config.py"

# File to store PIDs and ports of running satellites
PID_FILE="satellite_pids.txt"

# Default IP address
DEFAULT_IP=""  # Empty means use the value from config.py

# Parse command line arguments
while getopts ":i:n:h" opt; do
  case $opt in
    i) CUSTOM_IP="$OPTARG" ;;
    n) CUSTOM_NUM_SATELLITES="$OPTARG" ;;
    h) 
       echo "Usage: $0 [-i IP_ADDRESS] [-n NUM_SATELLITES] [-h]"
       echo "  -i IP_ADDRESS     IP address to bind satellites (default: value from config.py)"
       echo "  -n NUM_SATELLITES Number of satellites to launch (default: value from config.py)"
       echo "  -h                Show this help message"
       exit 0
       ;;
    \?) echo "Invalid option: -$OPTARG" >&2; exit 1 ;;
    :) echo "Option -$OPTARG requires an argument." >&2; exit 1 ;;
  esac
done

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
NUM_SATELLITES=${CUSTOM_NUM_SATELLITES:-$(python3 -c "import sys; sys.path.append('$(dirname $CONFIG_FILE)'); import config; print(config.NUM_SATELLITES)")}
SATELLITE_IP=${CUSTOM_IP:-$(python3 -c "import sys; sys.path.append('$(dirname $CONFIG_FILE)'); import config; print(config.SATELLITE_IP)")}

echo "Launching $NUM_SATELLITES satellites..."

# Launch satellites on consecutive ports
for ((i = 0; i < NUM_SATELLITES; i++)); do
    PORT=$((START_PORT + i))
    echo "Starting satellite on $SATELLITE_IP:$PORT..."
    python3 $SATELLITE_SCRIPT --ip $SATELLITE_IP --port $PORT &
    PID=$!
    
    # Check if satellite process is running
    if ps -p $PID > /dev/null; then
        echo "$PID $PORT" >> "$PID_FILE"  # Save PID and port to the file
        echo "Satellite on port $PORT started successfully with PID $PID."
    else
        echo "Error: Failed to start satellite on port $PORT!"
    fi
done

echo "All satellites launched successfully!"
echo "To stop satellites: ./stop_satellites.sh"
