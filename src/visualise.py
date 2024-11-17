from flask import Flask, jsonify, send_from_directory
import requests
import math
import sys

SHIP_PORT = 8001

sys.path.append("/home/zia/Documents/sc_project3/src")  # Update to your project path
from config import COMMUNICATION_RANGE_KM, GROUND_CONTROL_COORDS, SATELLITE_PORTS, GROUND_CONTROL_COORDS

# Flask app for visualization
app = Flask(__name__)

# Function to fetch position from a given server
def fetch_position(port):
    try:
        response = requests.get(f"http://127.0.0.1:{port}/get-position")
        if response.status_code == 200:
            data = response.json()
            return data["latitude"], data["longitude"]
    except requests.ConnectionError:
        return None
    return None

# Calculate the distance between two coordinates using the haversine formula
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Radius of the Earth in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

@app.route('/get-all-positions', methods=['GET'])
def get_all_positions():
    positions = {
        "satellites": [],
        "ship": None,
        "edges": [],
        "ground_control": {"latitude": GROUND_CONTROL_COORDS[0], "longitude": GROUND_CONTROL_COORDS[1]},
    }

    # Fetch satellite positions
    for port in SATELLITE_PORTS:
        position = fetch_position(port)
        if position:
            positions["satellites"].append({"latitude": position[0], "longitude": position[1], "port": port})

    # Fetch ship position
    ship_position = fetch_position(SHIP_PORT)
    if ship_position:
        positions["ship"] = {"latitude": ship_position[0], "longitude": ship_position[1]}

    # Compute edges between neighbors
    all_positions = [{"latitude": positions["ground_control"]["latitude"], "longitude": positions["ground_control"]["longitude"], "type": "ground_control"}]
    all_positions += [{"latitude": sat["latitude"], "longitude": sat["longitude"], "type": "satellite", "port": sat["port"]} for sat in positions["satellites"]]
    if positions["ship"]:
        all_positions.append({"latitude": positions["ship"]["latitude"], "longitude": positions["ship"]["longitude"], "type": "ship"})

    for i, source in enumerate(all_positions):
        for target in all_positions[i + 1:]:
            distance = haversine(source["latitude"], source["longitude"], target["latitude"], target["longitude"])
            if distance <= COMMUNICATION_RANGE_KM:
                positions["edges"].append({"source": source, "target": target})

    return jsonify(positions)

@app.route('/')
def visualize():
    return send_from_directory('templates', 'index.html')

if __name__ == '__main__':
    app.run(debug=True, port=8069)
