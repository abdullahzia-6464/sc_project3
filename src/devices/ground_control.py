from flask import Flask, request, jsonify
import csv
from pathlib import Path

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
        writer.writerow(["fish_count", "wind_level", "water_temp", "water_depth"])

@app.route("/", methods=["POST"])
def receive_data():
    data = request.get_json()

    # Validate data payload
    if "payload" in data:
        payload = data["payload"]
        print(f"Ground Control received data: {payload}")

        # Save data to CSV
        with open(OUTPUT_FILE, mode="a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([
                payload.get("caught_fish", "N/A"),
                payload.get("wind_levels", "N/A"),
                payload.get("water_temperature", "N/A"),
                payload.get("water_depth", "N/A"),
            ])

        return jsonify({"status": "Data received"}), 200

    return jsonify({"status": "Invalid data format"}), 400

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)  # Ground control listens on port 8000
