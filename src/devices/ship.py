from flask import Flask, jsonify
import requests
import random
import time
import math
import sys

sys.path.append("/home/zia/Documents/sc_project3/src")  # Update to your project path
from config import SATELLITE_PORTS, TIME_STEP

# Circular trajectory parameters for the ship
CENTER_LAT, CENTER_LON = 50.89, -8.68  # Starting position for the ship
SHIP_SPEED = 0.01  # Degrees per time step

app = Flask(__name__)

class Ship:
    def __init__(self):
        self.latitude = CENTER_LAT
        self.longitude = CENTER_LON

    def move(self):
        # The ship moves in a slow zigzag pattern across the Celtic Sea
        self.latitude += SHIP_SPEED * 0.1  # Slight change in latitude
        self.longitude += SHIP_SPEED  # Larger change in longitude
        print(f"Ship moved to lat={self.latitude}, lon={self.longitude}")

    def find_nearest_satellite(self):
        nearest_satellite = None
        nearest_distance = float("inf")
        for port in SATELLITE_PORTS:
            try:
                response = requests.get(f"http://127.0.0.1:{port}/get-position")
                position = response.json()
                distance = haversine(self.latitude, self.longitude, position["latitude"], position["longitude"])
                if distance < nearest_distance:
                    nearest_distance = distance
                    nearest_satellite = port
            except Exception:
                continue
        return nearest_satellite

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
        nearest_satellite = self.find_nearest_satellite()
        if nearest_satellite:
            try:
                response = requests.post(f"http://127.0.0.1:{nearest_satellite}/", json=data)
                print(f"Ship sent data to Satellite {nearest_satellite}. Response: {response.json()}")
            except Exception as e:
                print(f"Error sending data to Satellite {nearest_satellite}: {e}")
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
