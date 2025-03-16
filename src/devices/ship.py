import argparse
from cryptography.fernet import Fernet
import json
from flask import Flask, jsonify
import requests
import random
import time
import sys
import os
import hashlib
import logging
from math import radians, sin, cos, sqrt, atan2
from threading import Thread

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ship')

# Import configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
from config import (
    SATELLITE_PORTS, TIME_STEP, GROUND_CONTROL_COORDS, COMMUNICATION_RANGE_KM, 
    SHIP_SPEED, SATELLITE_IP, EARTH_DEVICE_IP, GROUND_CONTROL_PORT, GROUP8_IP
)

# Ship starting position
CENTER_LAT, CENTER_LON = 49.6, -8.68

# Celtic Sea boundary coordinates
LAT_MIN, LAT_MAX = 49.5, 51.0
LON_MIN, LON_MAX = -11.0, -7.5

app = Flask(__name__)

def calculate_checksum(data):
    """Calculate MD5 checksum of the given data."""
    data_str = str(data).encode('utf-8')
    return hashlib.md5(data_str).hexdigest()

def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance between two points on Earth using haversine formula."""
    R = 6371  # Earth radius in kilometers
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def log_communication(source, target):
    """Log communication events for visualization."""
    url = f"http://{EARTH_DEVICE_IP}:33069/log-communication"
    data = {
        "source": {"latitude": source[0], "longitude": source[1]},
        "target": {"latitude": target[0], "longitude": target[1]},
    }
    try:
        requests.post(url, json=data, proxies={"http": None, "https": None}, timeout=2)
    except requests.RequestException:
        logger.debug("Failed to log communication")

class Ship:
    def __init__(self, port):
        """Initialize a ship with the given port number."""
        self.latitude = CENTER_LAT
        self.longitude = CENTER_LON
        self.neighbors = []  # List of satellites within communication range
        self.speed = SHIP_SPEED
        self.direction = 1  # Direction multiplier (1 or -1)
        self.port = port
        self.ship_id = str(port)[-2:]
        self.last_sent_time = 0
        self.retry_count = 0
        self.max_retries = 3
        logger.info(f"Ship {self.ship_id} initialized at ({self.latitude}, {self.longitude})")

    def move(self):
        """Update the ship's position in a zigzag pattern within the Celtic Sea."""
        # Calculate new position
        new_lat = self.latitude + self.speed * 0.1 * self.direction
        new_lon = self.longitude + self.speed * self.direction

        # Check if the new position is within the Celtic Sea boundary
        if self.is_within_celtic_sea(new_lat, new_lon):
            self.latitude = new_lat
            self.longitude = new_lon
        else:
            # Reverse direction to stay within the boundary
            self.direction *= -1  # Flip direction
            logger.debug(f"Ship {self.ship_id} reversed direction to stay within boundary")

        # Find satellites within communication range
        self.find_neighbors()

    def is_within_celtic_sea(self, lat, lon):
        """Check if the given coordinates are within the Celtic Sea boundary."""
        return LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX

    def find_neighbors(self):
        """Find satellites within communication range."""
        self.neighbors = []
        for port in SATELLITE_PORTS:
            try:
                response = requests.get(
                    f"http://{SATELLITE_IP}:{port}/get-position", 
                    proxies={"http": None, "https": None},
                    timeout=2
                )
                if response.status_code == 200:
                    position = response.json()
                    distance = haversine(
                        self.latitude, self.longitude, 
                        position["latitude"], position["longitude"]
                    )
                    if distance <= COMMUNICATION_RANGE_KM:
                        self.neighbors.append((port, distance))
            except requests.RequestException:
                continue

    def find_closest_to_ground_control(self):
        """Find the satellite closest to ground control from neighbors."""
        ground_lat, ground_lon = GROUND_CONTROL_COORDS
        closest_port = None
        closest_distance = float("inf")

        for port, _ in self.neighbors:
            try:
                response = requests.get(
                    f"http://{SATELLITE_IP}:{port}/get-position", 
                    proxies={"http": None, "https": None},
                    timeout=2
                )
                if response.status_code != 200:
                    continue
                    
                position = response.json()
                distance_to_ground = haversine(
                    position["latitude"], position["longitude"], 
                    ground_lat, ground_lon
                )
                if distance_to_ground < closest_distance:
                    closest_distance = distance_to_ground
                    closest_port = port
            except requests.RequestException:
                continue
                
        return closest_port

    def create_data_packet(self):
        """Create a data packet with ship telemetry."""
        current_time = time.time()
        
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

        # Introduce random corruption for testing checksum validation
        if random.random() < 0.2:  # 20% probability
            decrypted_payload = json.loads(cipher_suite.decrypt(data["payload"].encode()).decode())
            decrypted_payload["caught_fish"] = "CORRUPTED"
            logger.warning("Payload corrupted for demonstration - ground control will discard this message")
            data["payload"] = cipher_suite.encrypt(json.dumps(decrypted_payload).encode()).decode()
            
        return data

    def send_data(self):
        """Generate and send data to the closest satellite."""
        current_time = time.time()
        
        # Only send data periodically
        if current_time - self.last_sent_time <= TIME_STEP * 5:
            return

        # Create headers for forwarding
        headers = {
            "X-Group-ID": "10",
            "X-Destination-IP": str(EARTH_DEVICE_IP),
            "X-Destination-Port": str(GROUND_CONTROL_PORT)
        }
            
        # Create data packet
        data = self.create_data_packet()
        
        # Handle interoperable mode
        if interoperable:
            try:
                response = requests.post(
                    f"http://{GROUP8_IP}:{33001}/", 
                    json=data, 
                    proxies={"http": None, "https": None}, 
                    headers=headers,
                    timeout=5
                )
                logger.info(f"Data sent to Group 8's satellite")
            except Exception as e:
                logger.error(f"Error sending data to Group 8's satellite: {e}")
            self.last_sent_time = current_time
            return

        # Find and send to closest satellite
        closest_satellite = self.find_closest_to_ground_control()
        if not closest_satellite:
            logger.warning("No satellite within range to send data")
            self.last_sent_time = current_time  # Still update time to avoid constant retries
            return
            
        try:
            # Send data to closest satellite
            response = requests.post(
                f"http://{SATELLITE_IP}:{closest_satellite}/", 
                json=data, 
                proxies={"http": None, "https": None}, 
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info(f"Message sent to satellite {closest_satellite}")
                
                # Log communication for visualization
                target_coords = requests.get(
                    f"http://{SATELLITE_IP}:{closest_satellite}/get-position", 
                    proxies={"http": None, "https": None}
                ).json()
                target = [target_coords["latitude"], target_coords["longitude"]]
                log_communication([self.latitude, self.longitude], target)
                
                # Process acknowledgment if needed
                # ack = response.json()
            else:
                logger.warning(f"Received non-200 response: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error sending data to Satellite {closest_satellite}: {e}")
            
        # Update last sent time regardless of success to avoid spam
        self.last_sent_time = current_time

@app.route("/get-position", methods=["GET"])
def get_position():
    """Endpoint to retrieve the current position of the ship."""
    return jsonify({
        "latitude": ship.latitude,
        "longitude": ship.longitude
    })

def ship_behavior():
    """Continuously update the ship's position and send data to the nearest satellite."""
    try:
        while True:
            ship.move()
            ship.send_data()
            time.sleep(TIME_STEP)
    except Exception as e:
        logger.error(f"Error in ship behavior thread: {e}")
        # Restart the thread if it fails
        time.sleep(5)
        Thread(target=ship_behavior, daemon=True).start()

if __name__ == "__main__":
    # Configure Flask to be less verbose
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.ERROR)

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run the ship server.")
    parser.add_argument("--port", type=int, required=True, help="Port for the ship server.")
    parser.add_argument("--ip", type=str, default="127.0.0.1",
                        help="IP address to bind the ship server (default: 127.0.0.1).")
    parser.add_argument("--interoperable", action="store_true",
                        help="Enable interoperability with Group 8's system.")
    args = parser.parse_args()

    # Set interoperability mode
    interoperable = args.interoperable

    # Initialize ship
    port = args.port
    ship = Ship(port=port)

    # Load the symmetric key
    try:
        with open("src/devices/symmetric.key", "rb") as key_file:
            key = key_file.read()
        cipher_suite = Fernet(key)
        logger.info("Symmetric key loaded successfully")
    except Exception as e:
        logger.error(f"Error loading symmetric key: {e}")
        sys.exit(1)

    # Start ship behavior thread
    logger.info(f"Starting ship {ship.ship_id} on port {port}")
    Thread(target=ship_behavior, daemon=True).start()
    
    # Start Flask server
    app.run(host=args.ip, port=port, debug=False)

