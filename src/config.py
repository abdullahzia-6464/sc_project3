# Configuration for the simulation
INITIAL_POSITIONS_FILE = "data/initial_positions.csv"

# Port assignments for devices (on localhost for testing)
GROUND_CONTROL_PORT = 8000
SHIP_PORT = 8001
SATELLITE_PORTS = range(8002, 8011)

GROUND_CONTROL_COORDS = [51.8985, -8.4756]
COMMUNICATION_RANGE_KM = 150 

# Simulation settings
TIME_STEP = 1  # Time step in seconds
SIMULATION_DURATION = 60  # Total simulation time in seconds
