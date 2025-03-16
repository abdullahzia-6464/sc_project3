import argparse
from cryptography.fernet import Fernet
import json
from flask import Flask, request, jsonify
import csv
from pathlib import Path
import time
from datetime import datetime
import sys
import os
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ground_control')

# Import configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from config import GROUND_CONTROL_PORT

# Import utility functions
from devices.ship import calculate_checksum

app = Flask(__name__)

# CSV file for storing received data
OUTPUT_FILE = "src/data/output_data.csv"

def ensure_output_file_exists():
    """Create output file with headers if it doesn't exist."""
    file_path = Path(OUTPUT_FILE)
    if not file_path.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.touch()

        with open(OUTPUT_FILE, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["ship_id", "timestamp_sent", "fish_count", "wind_level", "water_temp", "water_depth", "delay"])
        logger.info(f"Created output file: {OUTPUT_FILE}")

def save_data_to_csv(data, timestamp, delay, payload):
    """Save received data to CSV file."""
    with open(OUTPUT_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            data.get("ship_id", "unknown"),
            datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S') if timestamp else "N/A",
            payload.get("caught_fish", "N/A"),
            payload.get("wind_levels", "N/A"),
            payload.get("water_temperature", "N/A"),
            payload.get("water_depth", "N/A"),
            delay,
        ])

@app.route("/", methods=["POST"])
def receive_data():
    """Handle incoming data from ships via satellites."""
    try:
        data = request.get_json()
        if not data:
            logger.warning("No data received")
            return jsonify({"status": "No data received"}), 400
            
        if "payload" not in data or "checksum" not in data:
            logger.warning("Invalid data format - missing payload or checksum")
            return jsonify({"status": "Invalid data format"}), 400
            
        try:
            # Decrypt the payload
            encrypted_payload = data["payload"].encode()
            decrypted_payload = cipher_suite.decrypt(encrypted_payload).decode()
            
            # Verify checksum
            received_checksum = data["checksum"]
            calculated_checksum = calculate_checksum(decrypted_payload)
            
            if received_checksum != calculated_checksum:
                logger.warning(f"Checksum mismatch for data from Ship {data.get('ship_id', 'unknown')}")
                return jsonify({"status": "Checksum Error"}), 400
                
            data["payload"] = json.loads(decrypted_payload)
            
        except (ValueError, json.JSONDecodeError) as e:
            logger.error(f"JSON parsing error: {e}")
            return jsonify({"status": "Invalid payload format"}), 400
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            return jsonify({"status": "Decryption Error"}), 400
            
        # Process the valid data
        payload = data["payload"]
        logger.info(f"Received data from Ship {data.get('ship_id', 'unknown')}")
        
        timestamp = data.get("timestamp")
        delay = round(time.time() - timestamp, 2) if timestamp else "Unknown"
        logger.info(f"Message delay: {delay} seconds")
        
        # Save data to CSV
        save_data_to_csv(data, timestamp, delay, payload)
        
        return jsonify({"status": "Acknowledged"}), 200
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({"status": "Server Error"}), 500


if __name__ == "__main__":
    # Argument parser for IP
    parser = argparse.ArgumentParser(description="Run the ground control server.")
    parser.add_argument("--ip", type=str, default="0.0.0.0",
                        help="IP address to bind the ground control server (default: 0.0.0.0).")
    parser.add_argument("--key-path", type=str, default="src/devices/symmetric.key",
                        help="Path to the symmetric key file.")
    args = parser.parse_args()

    # Ensure output file exists
    ensure_output_file_exists()

    # Load the symmetric key
    try:
        with open(args.key_path, "rb") as key_file:
            key = key_file.read()
        cipher_suite = Fernet(key)
        logger.info("Symmetric key loaded successfully")
    except FileNotFoundError:
        logger.error(f"Key file not found at {args.key_path}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error loading key: {e}")
        sys.exit(1)

    # Start the Flask server
    logger.info(f"Starting ground control server on {args.ip}:{GROUND_CONTROL_PORT}")
    app.run(host=args.ip, port=GROUND_CONTROL_PORT)
