# Path for initial positions data
INITIAL_POSITIONS_FILE = "data/initial_positions.csv"

# Network configurations
GROUP8_IP = '10.35.70.11'
SATELLITE_IP = '127.0.0.1'
EARTH_DEVICE_IP = '127.0.0.1'

# Port configurations
GROUND_CONTROL_PORT = 33000
SHIP_PORT = range(33001, 33006)
SATELLITE_PORTS = range(33007, 33017)
START_PORT = SATELLITE_PORTS[0]
NUM_SATELLITES = 6

# Geographic parameters
GROUND_CONTROL_COORDS = [51.8985, -8.4756]
COMMUNICATION_RANGE_KM = 180

# Movement parameters
SHIP_SPEED = 0.02

# Simulation settings
TIME_STEP = 1  # Time step in seconds
SIMULATION_DURATION = 60  # Total simulation time in seconds

# Visualization settings
COMMUNICATION_DISPLAY_TIME = 1  # Time to display communication lines (seconds)
