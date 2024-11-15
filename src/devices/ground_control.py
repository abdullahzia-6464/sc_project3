from flask import Flask, request, jsonify
import csv
import os
from pathlib import Path

app = Flask(__name__)
OUTPUT_FILE = "src/data/output_data.csv"

# Initialize the output file
# dir = os.path.dirname(OUTPUT_FILE) 
# if os.path.exists(dir):
#     os.makedirs(dir)
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
    print(f"Ground Control received data: {data}")

    # Save data to CSV
    with open(OUTPUT_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([data["fish_count"], data["wind_level"], data["water_temp"], data["water_depth"]])

    return jsonify({"status": "Data received"})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)
