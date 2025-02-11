import argparse
from cryptography.fernet import Fernet
import json
from flask import Flask, jsonify
import requests
import random
import time
import sys
#from shapely.geometry import Point, Polygon
import os
import hashlib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from config import SATELLITE_PORTS, TIME_STEP, GROUND_CONTROL_COORDS, COMMUNICATION_RANGE_KM, SHIP_SPEED, SATELLITE_IP, EARTH_DEVICE_IP, GROUND_CONTROL_PORT, GROUP8_IP


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
        # self.celtic_sea_boundary = Polygon([
        #     (51.0, -11.0),  # Bottom-left corner
        #     (51.0, -7.5),   # Bottom-right corner
        #     (49.5, -7.5),   # Top-right corner
        #     (49.5, -11.0)   # Top-left corner
        # ])

        self.port = port
        self.ship_id = str(port)[-2:]
        self.last_ack = None
        self.last_sent_time = 0

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
        return 49.5 <= lat <= 51.0 and -11.0 <= lon <= -7.5


    def find_neighbors(self):
        self.neighbors = []
        for port in SATELLITE_PORTS:
            try:
                response = requests.get(f"http://{SATELLITE_IP}:{port}/get-position", proxies={"http": None, "https": None})
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
                response = requests.get(f"http://{SATELLITE_IP}:{port}/get-position", proxies={"http": None, "https": None})
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
        headers = {
            "X-Group-ID": "10",
            "X-Destination-IP" : str(EARTH_DEVICE_IP),
            "X-Destination-Port" : str(GROUND_CONTROL_PORT)
        }
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

            # Serialize and encrypt the payload
            payload_str = json.dumps(data["payload"])
            encrypted_payload = cipher_suite.encrypt(payload_str.encode())
            data["payload"] = encrypted_payload.decode()

            # Calculate checksum
            data["checksum"] = calculate_checksum(payload_str)

            # Introduce random corruption
            if random.random() < 0.2:  # 20% probability
                decrypted_payload = json.loads(cipher_suite.decrypt(data["payload"].encode()).decode())
                decrypted_payload["caught_fish"] = "CORRUPTED"
                print("*************")
                print("Payload corrupted for demonstration. Ground control will discard this message after checking checksum.")
                print("*************")
                data["payload"] = cipher_suite.encrypt(json.dumps(decrypted_payload).encode()).decode()

            if interoperable:
                try:
                    response = requests.post(f"http://{GROUP8_IP}:{33001}/", json=data, proxies={"http": None, "https": None}, headers=headers)
                except Exception as e:
                    print(f"Error sending data to group 8's satellite :(")
                return


            closest_satellite = self.find_closest_to_ground_control()
            if closest_satellite:
                try:
                    response = requests.post(f"http://{SATELLITE_IP}:{closest_satellite}/", json=data, proxies={"http": None, "https": None}, headers=headers)
                    print(f"Message sent to satellite {SATELLITE_IP}:{closest_satellite}")
                    # call log_communication to visualise the comm
                    target_coords = requests.get(f"http://{SATELLITE_IP}:{closest_satellite}/get-position", proxies={"http": None, "https": None}).json()
                    target = [target_coords["latitude"], target_coords["longitude"]]
                    #print("LOGGING COMMS")
                    log_communication([ship.latitude, ship.longitude],target)

                    ack = response.json()
                    # if ack.get("status") == "Acknowledged":
                    #     self.last_ack = ack
                    #     print(f"Received acknowledgment: {ack}")
                    # else:
                    #     print("Acknowledgment not received, retrying...")
                except Exception as e:
                    print(f"Error sending data to Satellite {closest_satellite}: {e}")
            else:
                print("No satellite within range to send data.")
            self.last_sent_time = current_time


def log_communication(source, target):
    url = f"http://{EARTH_DEVICE_IP}:33069/log-communication"
    data = {
        "source": {"latitude": source[0], "longitude": source[1]},
        "target": {"latitude": target[0], "longitude": target[1]},
    }
    try:
        requests.post(url, json=data, proxies={"http": None, "https": None})
    except requests.ConnectionError:
        print()

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
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)  # Suppress GET/POST logs

    parser = argparse.ArgumentParser(description="Run the ship server.")
    parser.add_argument("--port", type=int, help="Port for the ship server.")
    parser.add_argument("--ip", type=str, default="127.0.0.1",
                        help="IP address of the ground control (default: 127.0.0.1).")
    args = parser.parse_args()

    port = args.port
    ship = Ship(port=port)

    global interoperable
    if len(sys.argv) == 4:
        interoperable = True
    else:
        interoperable = False

    port = args.port
    ship = Ship(port=port)

    # Load the symmetric key
    with open("src/devices/symmetric.key", "rb") as key_file:
        key = key_file.read()
    cipher_suite = Fernet(key)

    from threading import Thread
    Thread(target=ship_behavior, daemon=True).start()
    app.run(host=args.ip, port=port)

