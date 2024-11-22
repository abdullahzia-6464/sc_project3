from flask import Flask, jsonify, send_from_directory, request
import math
import sys
import time
import requests
import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
#sys.path.append("/Users/korayyesilova/Desktop/sc_project3/src")  # Update to your project path
from config import COMMUNICATION_RANGE_KM, SHIP_PORT, SATELLITE_PORTS, GROUND_CONTROL_COORDS, EARTH_DEVICE_IP, SATELLITE_IP

# Shared data to track active communications
active_communications = []

COMMUNICATION_DISPLAY_TIME = 1  # Time in seconds to display a communication line

# Flask app for visualization
app = Flask(__name__)

# Function to fetch position from a given server
def fetch_position(ip, port):
    try:
        response = requests.get(f"http://{ip}:{port}/get-position", proxies={"http": None, "https": None}, timeout=5)
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
    # Remove expired communication events
    global active_communications
    current_time = time.time()
    active_communications = [
        comm for comm in active_communications
        if current_time - comm["timestamp"] <= COMMUNICATION_DISPLAY_TIME
    ]

    positions = {
        "satellites": [],
        "ship": None,
        "edges": [],
        "communications": active_communications,  # Add active communications
        "ground_control": {"latitude": GROUND_CONTROL_COORDS[0], "longitude": GROUND_CONTROL_COORDS[1]},
    }

    # Fetch satellite positions
    for port in SATELLITE_PORTS:
        position = fetch_position(SATELLITE_IP, port)
        if position:
            positions["satellites"].append({"latitude": position[0], "longitude": position[1], "port": port})

    # Fetch ship position
    ship_position = fetch_position(EARTH_DEVICE_IP, SHIP_PORT[0])
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


@app.route('/log-communication', methods=['POST'])
def log_communication():
    data = request.get_json()
    source = data.get("source")
    target = data.get("target")
    timestamp = time.time()
    active_communications.append({"source": source, "target": target, "timestamp": timestamp})
    #print("Communication Logged.")
    return jsonify({"status": "logged"}), 200


@app.route('/')
def visualize():
    return send_from_directory('templates', 'index.html')

if __name__ == '__main__':
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)  # Suppress GET/POST logs

    app.run(debug=True, host='0.0.0.0', port=33069)
