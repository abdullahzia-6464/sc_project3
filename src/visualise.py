from flask import Flask, jsonify, send_from_directory
import requests

# Constants
CENTER_LAT = 51.9  # Approximate latitude of Cork, Ireland
CENTER_LON = -8.5  # Approximate longitude of Cork, Ireland
RADIUS_KM = 200  # Restricted radius in kilometers
SHIP_PORT = 8001
SATELLITE_PORTS = range(8002, 8011)  # Ports 8002 to 8010 for satellites

# Flask app for visualization
app = Flask(__name__)

# Function to fetch position from a given server
def fetch_position(port):
    try:
        response = requests.get(f"http://127.0.0.1:{port}/get-position")
        if response.status_code == 200:
            data = response.json()
            return data["latitude"], data["longitude"]
    except requests.ConnectionError:
        return None  # Server not running on this port
    return None  # Invalid response

@app.route('/get-all-positions', methods=['GET'])
def get_all_positions():
    positions = {
        "satellites": [],
        "ship": None
    }

    # Fetch satellite positions
    for port in SATELLITE_PORTS:
        position = fetch_position(port)
        if position:
            positions["satellites"].append({"latitude": position[0], "longitude": position[1], "port": port})

    # Fetch ship position
    ship_position = fetch_position(SHIP_PORT)
    if ship_position:
        positions["ship"] = {"latitude": ship_position[0], "longitude": ship_position[1]}

    return jsonify(positions)

@app.route('/')
def visualize():
    print("Visualise route accessed.")
    return send_from_directory('templates', 'index.html')

# # Function to create a folium map
# @app.route('/')
# def visualize():
#     # Create the map centered on the Celtic Sea area
#     folium_map = folium.Map(location=[CENTER_LAT, CENTER_LON], zoom_start=8)

#     # Add a circle to visualize the restricted region (Celtic Sea)
#     folium.Circle(
#         location=[CENTER_LAT, CENTER_LON],
#         radius=RADIUS_KM * 1000,  # Convert km to meters for Folium
#         color="blue",
#         fill=True,
#         fill_opacity=0.2,
#         tooltip="Celtic Sea Restricted Region"
#     ).add_to(folium_map)

#     # Fetch and display satellite positions
#     for port in SATELLITE_PORTS:
#         position = fetch_position(port)
#         if position:
#             lat, lon = position
#             folium.CircleMarker(
#                 location=[lat, lon],
#                 radius=8,  # Red circle size
#                 color="red",
#                 fill=True,
#                 fill_opacity=0.8,
#                 popup=f"Satellite (Port {port})"
#             ).add_to(folium_map)

#     # Fetch and display ship position
#     ship_position = fetch_position(SHIP_PORT)
#     if ship_position:
#         lat, lon = ship_position
#         folium.Marker(
#             location=[lat, lon],
#             popup="Ship",
#             icon=folium.Icon(color="blue", icon="ship")
#         ).add_to(folium_map)

#     return folium_map._repr_html_()

if __name__ == '__main__':
    app.run(debug=True, port=8069)
