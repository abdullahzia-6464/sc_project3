# Configuration for the simulation
INITIAL_POSITIONS_FILE = "data/initial_positions.csv"

#10.35.70.PI
SATELLITE_IP = '10.35.70.34'

EARTH_DEVICE_IP = '10.35.70.13'

GROUP8_IP = '10.35.70.11'

# SATELLITE_IP = '127.0.0.1'

# EARTH_DEVICE_IP = '127.0.0.1'

# Port assignments for devices (on localhost for testing)
GROUND_CONTROL_PORT = 33000
SHIP_PORT = range(33001, 33006)
SATELLITE_PORTS = range(33002, 33012)

GROUND_CONTROL_COORDS = [51.8985, -8.4756]
COMMUNICATION_RANGE_KM = 180 

SHIP_SPEED = 0.02

# Simulation settings
TIME_STEP = 1  # Time step in seconds
SIMULATION_DURATION = 60  # Total simulation time in seconds
