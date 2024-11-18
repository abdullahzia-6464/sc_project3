#!/bin/bash

# Script to stop a satellite server by port number.

# File containing PIDs and ports of satellites
PID_FILE="satellite_pids.txt"

if [ $# -ne 1 ]; then
    echo "Usage: $0 <port_number>"
    exit 1
fi

PORT=$1

if [ ! -f "$PID_FILE" ]; then
    echo "No satellites are running or PID file is missing."
    exit 1
fi

# Find the PID for the given port
FOUND=false
while IFS=' ' read -r pid port; do
    if [ "$port" -eq "$PORT" ]; then
        echo "Stopping satellite on port $port (PID $pid)..."
        kill "$pid" 2>/dev/null
        FOUND=true
        break
    fi
done < "$PID_FILE"

# Update the PID file to remove the stopped process
if $FOUND; then
    grep -v " $PORT\$" "$PID_FILE" > "${PID_FILE}.tmp" && mv "${PID_FILE}.tmp" "$PID_FILE"
    echo "Satellite on port $PORT stopped successfully."
else
    echo "No satellite running on port $PORT."
fi
