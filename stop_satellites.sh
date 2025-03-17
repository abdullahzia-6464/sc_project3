#!/bin/bash

# Script to stop all running satellite servers.

# File containing PIDs and ports of satellites
PID_FILE="satellite_pids.txt"

if [ ! -f "$PID_FILE" ]; then
    echo "No satellites are running or PID file is missing."
    exit 1
fi

# Count satellites to stop
SATELLITE_COUNT=$(wc -l < "$PID_FILE")
echo "Stopping $SATELLITE_COUNT satellites..."

STOPPED_COUNT=0
FAILED_COUNT=0

# Kill each process
while IFS=' ' read -r pid port; do
    echo "Stopping satellite on port $port (PID $pid)..."
    
    # Check if process is still running
    if ps -p "$pid" > /dev/null; then
        kill "$pid" 2>/dev/null
        
        # Wait briefly and check if process was terminated
        sleep 1
        if ! ps -p "$pid" > /dev/null; then
            echo "✓ Successfully stopped satellite on port $port"
            STOPPED_COUNT=$((STOPPED_COUNT + 1))
        else
            echo "! Satellite on port $port did not stop gracefully, forcing termination..."
            kill -9 "$pid" 2>/dev/null
            
            if ! ps -p "$pid" > /dev/null; then
                echo "✓ Force-stopped satellite on port $port"
                STOPPED_COUNT=$((STOPPED_COUNT + 1))
            else
                echo "✗ Failed to stop satellite on port $port"
                FAILED_COUNT=$((FAILED_COUNT + 1))
            fi
        fi
    else
        echo "! Process $pid was not running"
        STOPPED_COUNT=$((STOPPED_COUNT + 1))
    fi
done < "$PID_FILE"

# Clean up
rm "$PID_FILE"
echo "-----------------------------------"
echo "Summary: $STOPPED_COUNT satellites stopped, $FAILED_COUNT failed"
if [ $FAILED_COUNT -eq 0 ]; then
    echo "All satellites stopped successfully."
else
    echo "Warning: Some satellites could not be stopped."
    echo "You may need to manually terminate remaining processes."
fi
