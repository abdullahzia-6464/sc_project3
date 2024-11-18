from flask import Flask, request, jsonify
import csv
from pathlib import Path
import time
from datetime import datetime

from src.devices.ship import calculate_checksum

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
        received_checksum = data["checksum"]
        calculated_checksum = calculate_checksum(data["payload"])

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
    app.run(host="127.0.0.1", port=8000)  # Ground control listens on port 8000
