from flask import Flask, request, jsonify
import math
import time
from threading import Thread
import requests
import sys
import os
import random

sys.path.append("/home/zia/Documents/sc_project3/src")  # Update to your path
from config import SATELLITE_PORTS, GROUND_CONTROL_PORT, TIME_STEP

app = Flask(__name__)

# Circular trajectory parameters
CENTER_LAT, CENTER_LON = 51.5, -9.5  # Center of the circle
RADIUS_KM = 10000  # Radius of the circle in km
COMMUNICATION_RANGE_KM = 50  # Range for neighbors in km
SATELLITE_SPEED = 2.5  # Movement speed multiplier

# Satellite State
class Satellite:
    def __init__(self, satellite_id, all_ports):
        self.id = satellite_id
        
        # Randomize CENTER_LAT and CENTER_LON within the Celtic Sea bounds
        self.center_lat = random.uniform(49.5, 52.0)
        self.center_lon = random.uniform(-10.5, -8.5)
        
        self.angle = random.uniform(0, 360)  # Random starting angle
        self.latitude = None
        self.longitude = None
        self.all_ports = all_ports  # List of all satellite ports
        self.neighbors = []  # Neighbors list
        self.moving_outward = random.choice([True, False])  # Zig-zag direction
        self.update_position()

    def update_position(self):
        angle_rad = math.radians(self.angle)
        EARTH_RADIUS_KM = 6371  # Earth radius
        
        # Use instance-specific center latitude and longitude
        self.latitude = self.center_lat + (RADIUS_KM / EARTH_RADIUS_KM) * math.cos(angle_rad)
        self.longitude = self.center_lon + (RADIUS_KM / (EARTH_RADIUS_KM * math.cos(math.radians(self.center_lat)))) * math.sin(angle_rad)

    def move(self):
        if self.moving_outward:
            self.angle += SATELLITE_SPEED
        else:
            self.angle -= SATELLITE_SPEED

        # Zig-zag path: Reverse direction if out of bounds
        if self.angle >= 360 or self.angle <= 0:
            self.moving_outward = not self.moving_outward

        self.update_position()
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

satellite = Satellite(
    satellite_id=int(input("Enter Satellite ID: ")),
    all_ports=SATELLITE_PORTS,
)

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
    if destination == "ground_control":
        try:
            response = requests.post(f"http://127.0.0.1:{GROUND_CONTROL_PORT}/", json=data)
            return jsonify({"status": "Message forwarded to ground control", "response": response.json()})
        except Exception as e:
            return jsonify({"status": "Error forwarding to ground control", "error": str(e)}), 500
    else:
        for neighbor in satellite.neighbors:
            try:
                response = requests.post(f"http://127.0.0.1:{neighbor}/", json=data)
                return jsonify({"status": "Message forwarded to next satellite", "response": response.json()})
            except Exception as e:
                continue
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
    Thread(target=position_updater, daemon=True).start()
    app.run(host="127.0.0.1", port=int(input("Enter port for this satellite: ")))
