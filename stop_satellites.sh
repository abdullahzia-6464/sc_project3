#!/bin/bash

# Script to stop all running satellite servers.

# File containing PIDs and ports of satellites
PID_FILE="satellite_pids.txt"

if [ ! -f "$PID_FILE" ]; then
    echo "No satellites are running or PID file is missing."
    exit 1
fi

# Kill each process
while IFS=' ' read -r pid port; do
    echo "Stopping satellite on port $port (PID $pid)..."
    kill "$pid" 2>/dev/null
done < "$PID_FILE"

# Clean up
rm "$PID_FILE"
echo "All satellites stopped."
