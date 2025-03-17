#!/bin/bash

# Script to stop a satellite server by port number.

# File containing PIDs and ports of satellites
PID_FILE="satellite_pids.txt"

# Show usage information
function show_usage {
    echo "Usage: $0 <port_number>"
    echo "  <port_number>  Port number of the satellite to stop"
    exit 1
}

# Check if port number argument was provided
if [ $# -ne 1 ]; then
    show_usage
fi

# Validate port number is numeric
if ! [[ "$1" =~ ^[0-9]+$ ]]; then
    echo "Error: Port number must be numeric."
    show_usage
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
        
        # Check if process is still running
        if ps -p "$pid" > /dev/null; then
            kill "$pid" 2>/dev/null
            
            # Wait briefly and check if process was terminated
            sleep 1
            if ! ps -p "$pid" > /dev/null; then
                echo "Satellite terminated successfully."
            else
                echo "Warning: Satellite process did not terminate immediately."
                echo "Attempting to force kill..."
                kill -9 "$pid" 2>/dev/null
            fi
        else
            echo "Process was not running. Removing from tracking file."
        fi
        
        FOUND=true
        break
    fi
done < "$PID_FILE"

# Update the PID file to remove the stopped process
if $FOUND; then
    grep -v " $PORT\$" "$PID_FILE" > "${PID_FILE}.tmp" && mv "${PID_FILE}.tmp" "$PID_FILE"
    echo "Satellite on port $PORT removed from tracking."
else
    echo "No satellite running on port $PORT."
fi
