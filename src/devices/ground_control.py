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

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
#sys.path.append("/home/zia/Documents/sc_project3/src")  # Update to your project path
from config import GROUND_CONTROL_PORT

from devices.ship import calculate_checksum

app = Flask(__name__)

# CSV file for storing received data
OUTPUT_FILE = "src/data/output_data.csv"

# Ensure the output file exists with the correct headers
file_path = Path(OUTPUT_FILE)
if not file_path.exists():
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.touch()

    with open(OUTPUT_FILE, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["ship_id", "timestamp_sent", "fish_count", "wind_level", "water_temp", "water_depth", "delay"])

@app.route("/", methods=["POST"])
def receive_data():
    data = request.get_json()
    if "payload" in data and "checksum" in data:
        try:
            # Decrypt the payload
            encrypted_payload = data["payload"].encode()
            decrypted_payload = cipher_suite.decrypt(encrypted_payload).decode()
            data["payload"] = json.loads(decrypted_payload)
        except Exception as e:
            print(f"Decryption failed: {e}")
            return jsonify({"status": "Decryption Error"}), 400

        received_checksum = data["checksum"]
        calculated_checksum = calculate_checksum(decrypted_payload)

        # Verify checksum
        if received_checksum != calculated_checksum:
            print(f"Checksum mismatch for data from Ship {data['ship_id']}")
            return jsonify({"status": "Checksum Error"}), 400

        payload = data["payload"]
        print(f"Received data from Ship {data['ship_id']}: {payload}")
        timestamp = data.get("timestamp")
        delay = round(time.time() - timestamp, 2) if timestamp else "Unknown"
        print(f"Message delay: {delay} seconds")

        # Save data to CSV
        with open(OUTPUT_FILE, mode="a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([
                data["ship_id"],
                datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S') if timestamp else "N/A",
                payload.get("caught_fish", "N/A"),
                payload.get("wind_levels", "N/A"),
                payload.get("water_temperature", "N/A"),
                payload.get("water_depth", "N/A"),
                delay,
            ])

        return jsonify({"status": "Acknowledged"}), 200
    return jsonify({"status": "Invalid data format"}), 400


if __name__ == "__main__":
    # Argument parser for IP
    parser = argparse.ArgumentParser(description="Run the ground control server.")
    parser.add_argument("--ip", type=str, default="0.0.0.0",
                        help="IP address to bind the ground control server (default: 0.0.0.0).")
    args = parser.parse_args()

    # Load the symmetric key
    with open("src/devices/symmetric.key", "rb") as key_file:
        key = key_file.read()
    cipher_suite = Fernet(key)

    app.run(host=args.ip, port=GROUND_CONTROL_PORT)  # Ground control listens on port 8000
