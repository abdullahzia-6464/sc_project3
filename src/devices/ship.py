from flask import Flask, jsonify
import requests
import random
import time
import math
import sys
from shapely.geometry import Point, Polygon
import hashlib

sys.path.append("/Users/korayyesilova/Desktop/sc_project3/src")  # Update to your project path
from config import SATELLITE_PORTS, TIME_STEP, GROUND_CONTROL_COORDS, COMMUNICATION_RANGE_KM, SHIP_SPEED

# Circular trajectory parameters for the ship
CENTER_LAT, CENTER_LON = 49.6, -8.68  # Starting position for the ship

app = Flask(__name__)

def calculate_checksum(data):
    """
    Calculates MD5 checksum of the given data.
    """
    data_str = str(data).encode('utf-8')
    return hashlib.md5(data_str).hexdigest()

class Ship:
    def __init__(self, port):
        self.latitude = CENTER_LAT
        self.longitude = CENTER_LON
        self.neighbors = []  # List of satellites within communication range
        self.speed = SHIP_SPEED
        # Define a bounding polygon for the Celtic Sea
        self.celtic_sea_boundary = Polygon([
            (51.0, -11.0),  # Bottom-left corner
            (51.0, -7.5),   # Bottom-right corner
            (49.5, -7.5),   # Top-right corner
            (49.5, -11.0)   # Top-left corner
        ])

        self.port = port
        self.ship_id = str(port)[-2:]
        self.last_ack = None
        self.last_sent_time = 0
        self.last_sent_data = None

    def move(self):
        # Move the ship in a zigzag pattern
        new_lat = self.latitude + self.speed * 0.1  # Slight change in latitude
        new_lon = self.longitude + self.speed  # Larger change in longitude

        # Check if the new position is within the Celtic Sea boundary
        if self.is_within_celtic_sea(new_lat, new_lon):
            self.latitude = new_lat
            self.longitude = new_lon
        else:
            # Reverse direction to stay within the boundary
            self.speed *= -1  # Flip direction
            #print(f"Ship reversed direction to stay within the Celtic Sea boundary.")

        #print(f"Ship moved to lat={self.latitude}, lon={self.longitude}")
        self.find_neighbors()

    def is_within_celtic_sea(self, lat, lon):
        """
        Check if the given latitude and longitude are within the Celtic Sea boundary.
        """
        point = Point(lat, lon)
        return self.celtic_sea_boundary.contains(point)

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
        #print(f"Neighbors within range: {self.neighbors}")

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
        current_time = time.time()
        # if self.last_ack is not None or current_time - self.last_sent_time > TIME_STEP * 5:
        if current_time - self.last_sent_time > TIME_STEP * 5:
            data = {
                "source": "ship",
                "ship_id": self.ship_id,
                "destination": "ground_control",
                "timestamp": current_time,
                "payload": {
                    "caught_fish": random.randint(0, 100),
                    "wind_levels": round(random.uniform(5.0, 20.0), 1),
                    "water_temperature": round(random.uniform(10.0, 15.0), 1),
                    "water_depth": round(random.uniform(50.0, 200.0), 1),
                }
            }
            # Calculate checksum
            data["checksum"] = calculate_checksum(data["payload"])

            # Introduce random corruption
            if random.random() < 0.05:  # 5% probability
                data["payload"]["caught_fish"] = "CORRUPTED"
                print("Payload corrupted for demonstration")

            # Store the last transmitted data
            self.last_sent_data = data

            closest_satellite = self.find_closest_to_ground_control()
            if closest_satellite:
                try:
                    response = requests.post(f"http://127.0.0.1:{closest_satellite}/", json=data)

                    # call log_communication to visualise the comm
                    target_coords = requests.get(f"http://127.0.0.1:{closest_satellite}/get-position").json()
                    target = [target_coords["latitude"], target_coords["longitude"]]
                    print("LOGGING COMMS")
                    log_communication([ship.latitude, ship.longitude],target)

                    ack = response.json()
                    # if ack.get("status") == "Acknowledged":
                    #     self.last_ack = ack
                    #     print(f"Received acknowledgment: {ack}")
                    if ack.get("response").get("status") == "Checksum Error" and ack.get("response").get("action") == "Resend":
                        print("Resending data due to checksum error...")
                        self.resend_data(closest_satellite)
                    # else:
                    #     print("Acknowledgment not received, retrying...")
                except Exception as e:
                    print(f"Error sending data to Satellite {closest_satellite}: {e}")
            else:
                print("No satellite within range to send data.")
            self.last_sent_time = current_time

    def resend_data(self, satellite_port):
        if self.last_sent_data:
            try:
                response = requests.post(f"http://127.0.0.1:{satellite_port}/", json=self.last_sent_data)
                ack = response.json()
                if ack.get("status") == "Acknowledged":
                    self.last_ack = ack
                    print(f"Resent data acknowledged: {ack}")
                else:
                    print("Resent data acknowledgment failed.")
            except Exception as e:
                print(f"Error resending data to Satellite {satellite_port}: {e}")

def log_communication(source, target):
    url = "http://127.0.0.1:8069/log-communication"
    data = {
        "source": {"latitude": source[0], "longitude": source[1]},
        "target": {"latitude": target[0], "longitude": target[1]},
    }
    try:
        requests.post(url, json=data)
    except requests.ConnectionError:
        print("Failed to log communication")

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
    if len(sys.argv) != 2:
        print("Usage: python ship.py <port>")
        sys.exit(1)

    port = int(sys.argv[1])
    ship = Ship(port=port)

    from threading import Thread
    Thread(target=ship_behavior, daemon=True).start()
    app.run(host="127.0.0.1", port=port)

