import argparse
from flask import Flask, request, jsonify
import time
from threading import Thread
import requests
import sys
import random
import os
import logging
from math import radians, sin, cos, sqrt, atan2

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('satellite')

# Import configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
#sys.path.append("/Users/korayyesilova/Desktop/sc_project3/src")  # Update to your path
from config import (
    SATELLITE_PORTS, GROUND_CONTROL_PORT, GROUND_CONTROL_COORDS, 
    TIME_STEP, COMMUNICATION_RANGE_KM, EARTH_DEVICE_IP, SATELLITE_IP
)

app = Flask(__name__)

# Satellite movement parameters
SATELLITE_SPEED = 2.5
LAT_MIN, LAT_MAX = 48.5, 52.5
LON_MIN, LON_MAX = -11.5, -5.83

def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance between two points on Earth using haversine formula."""
    R = 6371  # Earth radius in kilometers
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

# Satellite State
class Satellite:
    def __init__(self, satellite_id, all_ports):
        self.id = satellite_id
        # Random initial position within specified range
        self.latitude = random.uniform(LAT_MIN, LAT_MAX)
        self.longitude = random.uniform(LON_MIN, LON_MAX)
        self.all_ports = all_ports
        self.neighbors = []
        self.moving_up_right = random.choice([True, False])
        self.step_size = 0.05
        logger.info(f"Satellite {self.id} initialized at ({self.latitude}, {self.longitude})")
        
    def move(self):
        """Update satellite position within boundaries."""
        # Calculate new position based on direction
        if self.moving_up_right:
            new_lat = self.latitude + self.step_size
            new_lon = self.longitude + self.step_size
        else:
            new_lat = self.latitude - self.step_size
            new_lon = self.longitude - self.step_size

        # Check if the new position is within boundaries
        if LAT_MIN <= new_lat <= LAT_MAX and LON_MIN <= new_lon <= LON_MAX:
            self.latitude = new_lat
            self.longitude = new_lon
        else:
            # Reverse direction if out of bounds
            self.moving_up_right = not self.moving_up_right
            logger.debug(f"Satellite {self.id} reversed direction to stay within boundaries")

        # Update list of neighboring satellites
        self.find_neighbors()

    def find_neighbors(self):
        """Find neighboring satellites within communication range."""
        self.neighbors = []
        for port in self.all_ports:
            if port != self.id:
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
                            self.neighbors.append(port)
                except (requests.exceptions.RequestException, ValueError):
                    pass

def find_closest_neighbor_to_ground_control():
    """Find the neighbor closest to ground control."""
    closest_neighbor = None
    closest_distance = float("inf")
    
    for neighbor in satellite.neighbors:
        try:
            response = requests.get(
                f"http://{SATELLITE_IP}:{neighbor}/get-position", 
                proxies={"http": None, "https": None},
                timeout=2
            )
            if response.status_code != 200:
                continue
                
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
            
    return closest_neighbor

@app.route("/", methods=["POST"])
def receive_message():
    """Handle incoming messages and route them toward ground control."""
    try:
        # Get message data
        data = request.get_json()
        if not data:
            logger.warning("Received empty message")
            return jsonify({"status": "No data received"}), 400
        
        # Add realistic network delay
        random_delay = random.uniform(0.1, 1.0)
        time.sleep(random_delay)
        
        # Set headers for forwarding
        headers = {
            "X-Group-ID": "10",
            "X-Destination-IP": EARTH_DEVICE_IP,
            "X-Destination-Port": str(GROUND_CONTROL_PORT)
        }

        # Check if we can reach ground control directly
        ground_control_distance = haversine(
            satellite.latitude, satellite.longitude,
            GROUND_CONTROL_COORDS[0], GROUND_CONTROL_COORDS[1]
        )
        
        # If within range of ground control, send directly
        if ground_control_distance <= COMMUNICATION_RANGE_KM:
            try:
                response = requests.post(
                    f"http://{EARTH_DEVICE_IP}:{GROUND_CONTROL_PORT}/", 
                    json=data, 
                    proxies={"http": None, "https": None},
                    timeout=5
                )
                log_communication([satellite.latitude, satellite.longitude], GROUND_CONTROL_COORDS)
                logger.info(f"Message sent to Ground Control")
                return jsonify({"status": "Message forwarded to ground control", "response": response.json()})
            except requests.exceptions.Timeout:
                logger.error("Timeout connecting to ground control")
                return jsonify({"status": "Timeout connecting to ground control"}), 504
            except Exception as e:
                logger.error(f"Error forwarding to ground control: {e}")
                return jsonify({"status": "Error forwarding to ground control", "error": str(e)}), 500

        # Find the best satellite to forward to
        closest_neighbor = find_closest_neighbor_to_ground_control()
        if not closest_neighbor:
            logger.warning("No neighbors available to forward message")
            return jsonify({"status": "No route to ground control"}), 404
        
        # Try to forward the message with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    f"http://{SATELLITE_IP}:{closest_neighbor}/", 
                    json=data, 
                    proxies={"http": None, "https": None},
                    timeout=5
                )
                
                if response.status_code == 200:
                    logger.info(f"Message forwarded to satellite {closest_neighbor}")
                    
                    # Log the communication for visualization
                    target_coords = requests.get(
                        f"http://{SATELLITE_IP}:{closest_neighbor}/get-position", 
                        proxies={"http": None, "https": None}
                    ).json()
                    target = [target_coords["latitude"], target_coords["longitude"]]
                    log_communication([satellite.latitude, satellite.longitude], target)
                    
                    return jsonify({"status": "Message forwarded", "response": response.json()}), 200
                
            except Exception as e:
                logger.warning(f"Attempt {attempt+1}/{max_retries} failed: {e}")
                
            # Wait before retry with exponential backoff
            retry_delay = 0.5 * (2 ** attempt)
            time.sleep(retry_delay)

        return jsonify({"status": "Message could not be forwarded after retries"}), 500
        
    except Exception as e:
        logger.error(f"Error in receive_message: {e}")
        return jsonify({"status": "Internal error", "error": str(e)}), 500

@app.route("/get-position", methods=["GET"])
def get_position():
    """Return current satellite position."""
    return jsonify({
        "latitude": satellite.latitude,
        "longitude": satellite.longitude
    })

def position_updater():
    """Periodic task to update satellite position."""
    while True:
        satellite.move()
        time.sleep(TIME_STEP)

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

if __name__ == "__main__":
    # Configure Flask to be less verbose
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.ERROR)

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run a satellite server.")
    parser.add_argument("--port", type=int, required=True, help="Port number for the satellite.")
    parser.add_argument("--ip", type=str, default="127.0.0.1",
                        help="IP address to bind the satellite (default: 127.0.0.1).")
    args = parser.parse_args()

    port = args.port
    ip = args.ip

    # Initialize satellite
    satellite = Satellite(
        satellite_id=port,
        all_ports=SATELLITE_PORTS,
    )

    # Start position updater thread
    Thread(target=position_updater, daemon=True).start()
    
    # Start Flask server
    logger.info(f"Starting satellite {port} on {ip}:{port}")
    app.run(debug=False, host=ip, port=port)
