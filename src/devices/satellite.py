from flask import Flask, request, jsonify
import math
import time
from threading import Thread
import requests
import sys
import random

sys.path.append("/home/zia/Documents/sc_project3/src")  # Update to your path
from config import SATELLITE_PORTS, GROUND_CONTROL_PORT, GROUND_CONTROL_COORDS, TIME_STEP, COMMUNICATION_RANGE_KM

app = Flask(__name__)

# Circular trajectory parameters
CENTER_LAT, CENTER_LON = 51.5, -9.5  # Center of the circle
RADIUS_KM = 10000  # Radius of the circle in km
SATELLITE_SPEED = 2.5  # Movement speed multiplier

# Satellite State
class Satellite:
    def __init__(self, satellite_id, all_ports):
        self.id = satellite_id
        # Random initial position within specified range
        self.latitude = random.uniform(48.5, 52.5)
        self.longitude = random.uniform(-11.5, -5.83)
        self.all_ports = all_ports
        self.neighbors = []
        self.moving_up_right = random.choice([True, False])  # Random initial direction
        self.step_size = 0.05  # Adjust this value for diagonal movement step size

    def move(self):
        # Adjust latitude and longitude based on direction
        if self.moving_up_right:
            new_lat = self.latitude + self.step_size
            new_lon = self.longitude + self.step_size
        else:
            new_lat = self.latitude - self.step_size
            new_lon = self.longitude - self.step_size

        # Check if the new position is within the specified boundaries
        if 48.5 <= new_lat <= 52.5 and -11.5 <= new_lon <= -5.83:
            # Update position if within bounds
            self.latitude = new_lat
            self.longitude = new_lon
        else:
            # Reverse direction if out of bounds
            self.moving_up_right = not self.moving_up_right
            print(f"Satellite {self.id} reversed direction to stay within boundaries.")

        self.find_neighbors()

    def find_neighbors(self):
        self.neighbors = []
        for port in self.all_ports:
            if port != self.id:
                try:
                    response = requests.get(f"http://127.0.0.1:{port}/get-position")
                    position = response.json()
                    distance = haversine(self.latitude, self.longitude, position["latitude"], position["longitude"])
                    if distance <= COMMUNICATION_RANGE_KM:
                        self.neighbors.append(port)
                except Exception:
                    pass

def haversine(lat1, lon1, lat2, lon2):
    from math import radians, sin, cos, sqrt, atan2
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

@app.route("/", methods=["POST"])
def receive_message():
    data = request.get_json()
    destination = data.get("destination")

    # Calculate distance to ground control
    ground_control_distance = haversine(
        satellite.latitude, satellite.longitude,
        GROUND_CONTROL_COORDS[0], GROUND_CONTROL_COORDS[1]
    )

    if destination == "ground_control" and ground_control_distance <= COMMUNICATION_RANGE_KM:
        try:
            response = requests.post(f"http://127.0.0.1:{GROUND_CONTROL_PORT}/", json=data)
            return jsonify({"status": "Message forwarded to ground control", "response": response.json()})
        except Exception as e:
            return jsonify({"status": "Error forwarding to ground control", "error": str(e)}), 500

    # Find a neighboring satellite closer to ground control
    closest_neighbor = None
    closest_distance = float("inf")
    for neighbor in satellite.neighbors:
        try:
            response = requests.get(f"http://127.0.0.1:{neighbor}/get-position")
            position = response.json()
            neighbor_distance = haversine(
                position["latitude"], position["longitude"],
                GROUND_CONTROL_COORDS[0], GROUND_CONTROL_COORDS[1]
            )
            if neighbor_distance < closest_distance:
                closest_distance = neighbor_distance
                closest_neighbor = neighbor
        except Exception:
            continue

    if closest_neighbor:
        try:
            response = requests.post(f"http://127.0.0.1:{closest_neighbor}/", json=data)
            return jsonify({"status": "Message forwarded to next satellite", "response": response.json()})
        except Exception as e:
            return jsonify({"status": "Error forwarding to next satellite", "error": str(e)}), 500

    return jsonify({"status": "Message could not be forwarded"}), 500

@app.route("/get-position", methods=["GET"])
def get_position():
    return jsonify({
        "latitude": satellite.latitude,
        "longitude": satellite.longitude
    })

def position_updater():
    while True:
        satellite.move()
        print(f"Satellite {satellite.id} moved to lat={satellite.latitude}, lon={satellite.longitude}")
        print(f"Neighbors: {satellite.neighbors}")
        time.sleep(TIME_STEP)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python satellite.py <port>")
        sys.exit(1)

    port = int(sys.argv[1])
    satellite = Satellite(
        satellite_id=port,
        all_ports=SATELLITE_PORTS,
    )

    Thread(target=position_updater, daemon=True).start()
    app.run(debug=True, host="127.0.0.1", port=port)
