import os
from flask import Flask, jsonify
import requests
import random
import time
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
from config import SATELLITE_PORTS, TIME_STEP, GROUND_CONTROL_COORDS, COMMUNICATION_RANGE_KM

# Boundary coordinates
BOUNDARY_COORDS = {
    "top_left": (51.038443, -10.861229),
    "top_right": (52.035308, -6.482007),
    "bottom_left": (49.343892, -9.612605),
    "bottom_right": (50.253625, -5.739909)
}

SHIP_SPEED = 0.05  # Degrees per time step

app = Flask(__name__)


class Ship:
    def __init__(self):
        # Initialize the ship at the center of the defined area
        self.latitude = (BOUNDARY_COORDS["top_left"][0] + BOUNDARY_COORDS["bottom_left"][0]) / 2
        self.longitude = (BOUNDARY_COORDS["top_left"][1] + BOUNDARY_COORDS["top_right"][1]) / 2
        self.neighbors = []  # List of satellites within communication range

    def move(self):
        # Randomize movement direction
        lat_change = random.uniform(-SHIP_SPEED, SHIP_SPEED)
        lon_change = random.uniform(-SHIP_SPEED, SHIP_SPEED)

        # Update position
        new_lat = self.latitude + lat_change
        new_lon = self.longitude + lon_change

        # Check if the new position is within the boundaries
        if (
                BOUNDARY_COORDS["bottom_left"][0] <= new_lat <= BOUNDARY_COORDS["top_left"][0] and
                BOUNDARY_COORDS["top_left"][1] <= new_lon <= BOUNDARY_COORDS["top_right"][1]
        ):
            # Update to new position if within bounds
            self.latitude = new_lat
            self.longitude = new_lon
        else:
            # Move in the opposite direction but stay close
            self.latitude += -lat_change * random.uniform(0.5, 1.0)  # Reverse direction and reduce magnitude
            self.longitude += -lon_change * random.uniform(0.5, 1.0)
            # Ensure still within bounds after the adjustment
            self.latitude = max(min(self.latitude, BOUNDARY_COORDS["top_left"][0]), BOUNDARY_COORDS["bottom_left"][0])
            self.longitude = max(min(self.longitude, BOUNDARY_COORDS["top_right"][1]), BOUNDARY_COORDS["top_left"][1])

        print(f"Ship moved to lat={self.latitude}, lon={self.longitude}")
        self.find_neighbors()

    def find_neighbors(self):
        self.neighbors = []
        for port in SATELLITE_PORTS:
            try:
                response = requests.get(f"http://127.0.0.1:{port}/get-position")
                position = response.json()
                distance = haversine(self.latitude, self.longitude, position["latitude"], position["longitude"])
                if distance <= COMMUNICATION_RANGE_KM:
                    self.neighbors.append((port, distance))
            except Exception:
                continue
        print(f"Neighbors within range: {self.neighbors}")

    def find_closest_to_ground_control(self):
        ground_lat, ground_lon = GROUND_CONTROL_COORDS
        closest_port = None
        closest_distance = float("inf")

        for port, _ in self.neighbors:
            try:
                response = requests.get(f"http://127.0.0.1:{port}/get-position")
                position = response.json()
                distance_to_ground = haversine(position["latitude"], position["longitude"], ground_lat, ground_lon)
                if distance_to_ground < closest_distance:
                    closest_distance = distance_to_ground
                    closest_port = port
            except Exception:
                continue
        return closest_port

    def send_data(self):
        data = {
            "source": "ship",
            "destination": "ground_control",
            "payload": {
                "caught_fish": random.randint(0, 100),
                "wind_levels": round(random.uniform(5.0, 20.0), 1),
                "water_temperature": round(random.uniform(10.0, 15.0), 1),
                "water_depth": round(random.uniform(50.0, 200.0), 1),
            }
        }
        self.find_neighbors()
        closest_satellite = self.find_closest_to_ground_control()
        if closest_satellite:
            try:
                response = requests.post(f"http://127.0.0.1:{closest_satellite}/", json=data)
                print(f"Ship sent data to Satellite {closest_satellite}. Response: {response.json()}")
            except Exception as e:
                print(f"Error sending data to Satellite {closest_satellite}: {e}")
        else:
            print("No satellite within range to send data.")


# Utility function to calculate the distance between two points
def haversine(lat1, lon1, lat2, lon2):
    from math import radians, sin, cos, sqrt, atan2
    R = 6371  # Earth radius in kilometers
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


@app.route("/get-position", methods=["GET"])
def get_position():
    """
    Endpoint to retrieve the current position of the ship.
    """
    return jsonify({
        "latitude": ship.latitude,
        "longitude": ship.longitude
    })


def ship_behavior():
    """
    Continuously update the ship's position and send data to the nearest satellite.
    """
    while True:
        ship.move()
        ship.send_data()
        time.sleep(TIME_STEP)


if __name__ == "__main__":
    ship = Ship()

    # Start the ship's behavior in a separate thread
    from threading import Thread

    Thread(target=ship_behavior, daemon=True).start()

    # Run the Flask server
    app.run(host="127.0.0.1", port=8001)  # Update port if needed
