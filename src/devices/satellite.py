from flask import Flask, request, jsonify
import requests
import sys
import os

sys.path.append("/home/zia/Documents/sc_project3/src") # TO FIX
from config import SATELLITE_PORTS, GROUND_CONTROL_PORT

app = Flask(__name__)

@app.route("/", methods=["POST"])
def handle_data():
    data = request.get_json()
    print(f"Satellite received data: {data}")

    # Forward data to next node in path
    next_port = GROUND_CONTROL_PORT  # Simplified for now (always forward to ground control)
    try:
        response = requests.post(f"http://127.0.0.1:{next_port}/", json=data)
        return jsonify({"status": "Data forwarded", "next_response": response.json()})
    except Exception as e:
        print(f"Error forwarding data: {e}")
        return jsonify({"status": "Error forwarding data", "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(input("Enter port for this satellite: ")))
