import requests
import random
import time
import sys

sys.path.append("/home/zia/Documents/sc_project3/src") # TO FIX

from config import SATELLITE_PORTS, TIME_STEP

def generate_data():
    return {
        "fish_count": random.randint(1, 100),
        "wind_level": round(random.uniform(0.1, 10.0), 1),
        "water_temp": round(random.uniform(5.0, 15.0), 1),
        "water_depth": random.randint(20, 500),
    }

def main():
    while True:
        data = generate_data()
        # Send data to the first satellite (simplified for now)
        satellite_port = SATELLITE_PORTS[0]
        try:
            response = requests.post(f"http://127.0.0.1:{satellite_port}/", json=data)
            print(f"Ship sent data to Satellite {satellite_port}: {response.json()}")
        except Exception as e:
            print(f"Error sending data to Satellite {satellite_port}: {e}")
        time.sleep(TIME_STEP)

if __name__ == "__main__":
    main()
