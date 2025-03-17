from flask import Flask, jsonify, send_from_directory, request
import math
import sys
import time
import requests
import os
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('visualizer')

# Import configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
#sys.path.append("/Users/korayyesilova/Desktop/sc_project3/src")  # Update to your project path
from config import (
    COMMUNICATION_RANGE_KM, SHIP_PORT, SATELLITE_PORTS, 
    GROUND_CONTROL_COORDS, EARTH_DEVICE_IP, SATELLITE_IP,
    COMMUNICATION_DISPLAY_TIME
)

# Shared data to track active communications
active_communications = []

# Flask app for visualization
app = Flask(__name__)

def fetch_position(ip, port, timeout=2):
    """
    Fetch position data from a server.
    
    Args:
        ip: Server IP address
        port: Server port
        timeout: Request timeout in seconds
        
    Returns:
        tuple: (latitude, longitude) or None if request failed
    """
    try:
        response = requests.get(
            f"http://{ip}:{port}/get-position", 
            proxies={"http": None, "https": None}, 
            timeout=timeout
        )
        if response.status_code == 200:
            data = response.json()
            return data["latitude"], data["longitude"]
    except (requests.ConnectionError, requests.Timeout):
        return None
    return None

def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two points using the haversine formula.
    
    Args:
        lat1, lon1: Coordinates of first point
        lat2, lon2: Coordinates of second point
        
    Returns:
        float: Distance in kilometers
    """
    R = 6371  # Radius of the Earth in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

@app.route('/get-all-positions', methods=['GET'])
def get_all_positions():
    """
    Get positions of all entities in the simulation.
    
    Returns:
        JSON with positions of satellites, ships, ground control,
        network edges, and active communications
    """
    # Clean up expired communications
    current_time = time.time()
    global active_communications
    active_communications = [
        comm for comm in active_communications
        if current_time - comm["timestamp"] <= COMMUNICATION_DISPLAY_TIME
    ]
    
    # Initialize result structure
    positions = {
        "satellites": [],
        "ship": None,
        "edges": [],
        "communications": active_communications,
        "ground_control": {
            "latitude": GROUND_CONTROL_COORDS[0], 
            "longitude": GROUND_CONTROL_COORDS[1]
        },
    }
    
    # Collect satellite positions
    satellites = fetch_satellite_positions()
    positions["satellites"] = satellites
    
    # Fetch ship position
    ship_position = fetch_position(EARTH_DEVICE_IP, SHIP_PORT[0])
    if ship_position:
        positions["ship"] = {
            "latitude": ship_position[0], 
            "longitude": ship_position[1]
        }
    
    # Calculate network edges
    positions["edges"] = calculate_network_edges(positions)
    
    return jsonify(positions)

def fetch_satellite_positions():
    """
    Fetch positions of all satellites.
    
    Returns:
        list: Satellite position data
    """
    satellites = []
    for port in SATELLITE_PORTS:
        position = fetch_position(SATELLITE_IP, port)
        if position:
            satellites.append({
                "latitude": position[0], 
                "longitude": position[1], 
                "port": port
            })
    return satellites

def calculate_network_edges(positions):
    """
    Calculate network edges between entities within communication range.
    
    Args:
        positions: Dict containing entity positions
        
    Returns:
        list: Edge data between connected entities
    """
    edges = []
    
    # Create list of all entities
    all_positions = [
        {
            "latitude": positions["ground_control"]["latitude"], 
            "longitude": positions["ground_control"]["longitude"], 
            "type": "ground_control"
        }
    ]
    
    all_positions += [
        {
            "latitude": sat["latitude"], 
            "longitude": sat["longitude"], 
            "type": "satellite", 
            "port": sat["port"]
        } 
        for sat in positions["satellites"]
    ]
    
    if positions["ship"]:
        all_positions.append({
            "latitude": positions["ship"]["latitude"], 
            "longitude": positions["ship"]["longitude"], 
            "type": "ship"
        })
    
    # Check which entities are within range of each other
    for i, source in enumerate(all_positions):
        for target in all_positions[i + 1:]:
            distance = haversine(
                source["latitude"], source["longitude"], 
                target["latitude"], target["longitude"]
            )
            if distance <= COMMUNICATION_RANGE_KM:
                edges.append({"source": source, "target": target})
    
    return edges

@app.route('/log-communication', methods=['POST'])
def log_communication():
    """Log a communication event between two entities."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "No data received"}), 400
            
        source = data.get("source")
        target = data.get("target")
        
        if not source or not target:
            return jsonify({"status": "Missing source or target"}), 400
            
        timestamp = time.time()
        active_communications.append({
            "source": source, 
            "target": target, 
            "timestamp": timestamp
        })
        
        logger.debug(f"Communication logged: {source} -> {target}")
        return jsonify({"status": "logged"}), 200
        
    except Exception as e:
        logger.error(f"Error logging communication: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/')
def visualize():
    """Serve the visualization interface."""
    return send_from_directory('templates', 'index.html')

if __name__ == '__main__':
    # Configure Flask to be less verbose
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.ERROR)

    # Start the visualization server
    logger.info("Starting visualization server on port 33069")
    app.run(debug=False, host='0.0.0.0', port=33069)
