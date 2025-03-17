#!/bin/bash

# Path to ship script
SHIP_SCRIPT="src/devices/ship.py"
CONFIG_FILE="src/config.py"

# Default IP address
DEFAULT_IP="127.0.0.1"

# Parse command line arguments
while getopts ":i:h" opt; do
  case $opt in
    i) IP="$OPTARG" ;;
    h) 
       echo "Usage: $0 [-i IP_ADDRESS] [-h] [--interoperable]"
       echo "  -i IP_ADDRESS    IP address to bind (default: 127.0.0.1)"
       echo "  -h               Show this help message"
       echo "  --interoperable  Enable interoperability with Group 8's system"
       exit 0
       ;;
    \?) echo "Invalid option: -$OPTARG" >&2; exit 1 ;;
    :) echo "Option -$OPTARG requires an argument." >&2; exit 1 ;;
  esac
done

# Shift processed options
shift $((OPTIND-1))

# Set IP if not already set by option
IP="${IP:-$DEFAULT_IP}"

# Check for interoperability flag
INTEROP_FLAG=""
if [[ "$1" == "--interoperable" ]]; then
    INTEROP_FLAG="--interoperable"
    echo "Running in interoperability mode..."
fi

# Retrieve ship port from config.py
START_PORT=$(python3 -c "import sys; sys.path.append('$(dirname $CONFIG_FILE)'); import config; print(config.SHIP_PORT[0])")

# Check if the script exists
if [[ ! -f $SHIP_SCRIPT ]]; then
    echo "Error: $SHIP_SCRIPT not found!"
    exit 1
fi

# Run the ship server
echo "Starting Ship on $IP:$START_PORT..."
python3 $SHIP_SCRIPT --port $START_PORT --ip $IP $INTEROP_FLAG
