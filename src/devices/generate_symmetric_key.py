from cryptography.fernet import Fernet
import os
import argparse
import sys

# Add path to the parent directory to import from src
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

def generate_key(output_path="symmetric.key"):
    """Generate a symmetric encryption key and save it to a file."""
    # Generate a key
    key = Fernet.generate_key()
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    # Write the key to file
    with open(output_path, "wb") as key_file:
        key_file.write(key)
    
    # Set restrictive permissions on Unix systems
    if os.name == 'posix':
        os.chmod(output_path, 0o600)
    
    print(f"Key generated and saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a symmetric encryption key")
    parser.add_argument("--output", default="src/devices/symmetric.key", 
                        help="Output file path for the key")
    args = parser.parse_args()
    
    generate_key(args.output)