#!/bin/bash

# Path to ground control script
GROUND_CONTROL_SCRIPT="src/devices/ground_control.py"
CONFIG_FILE="src/config.py"

# Default IP address
DEFAULT_IP="127.0.0.1"
# Default key path
DEFAULT_KEY_PATH="src/devices/symmetric.key"

# Parse command line arguments
while getopts ":i:k:h" opt; do
  case $opt in
    i) IP="$OPTARG" ;;
    k) KEY_PATH="$OPTARG" ;;
    h) 
       echo "Usage: $0 [-i IP_ADDRESS] [-k KEY_PATH] [-h]"
       echo "  -i IP_ADDRESS    IP address to bind (default: 127.0.0.1)"
       echo "  -k KEY_PATH      Path to the symmetric key file (default: src/devices/symmetric.key)"
       echo "  -h               Show this help message"
       exit 0
       ;;
    \?) echo "Invalid option: -$OPTARG" >&2; exit 1 ;;
    :) echo "Option -$OPTARG requires an argument." >&2; exit 1 ;;
  esac
done

# Set defaults if not specified
IP="${IP:-$DEFAULT_IP}"
KEY_PATH="${KEY_PATH:-$DEFAULT_KEY_PATH}"

# Check if key file exists
if [[ ! -f $KEY_PATH ]]; then
    echo "Warning: Symmetric key file not found at $KEY_PATH"
    echo "Generating a new key..."
    python3 src/devices/generate_symmetric_key.py --output "$KEY_PATH"
fi

# Retrieve port from config.py
GROUND_CONTROL_PORT=$(python3 -c "import sys; sys.path.append('$(dirname $CONFIG_FILE)'); import config; print(config.GROUND_CONTROL_PORT)")

# Check if the script exists
if [[ ! -f $GROUND_CONTROL_SCRIPT ]]; then
    echo "Error: $GROUND_CONTROL_SCRIPT not found!"
    exit 1
fi

# Run the ground control server
echo "Starting Ground Control on $IP:$GROUND_CONTROL_PORT..."
python3 $GROUND_CONTROL_SCRIPT --ip $IP --key-path "$KEY_PATH"
