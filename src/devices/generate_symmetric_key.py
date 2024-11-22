from cryptography.fernet import Fernet

# Generate a key (do this once and securely store it)
key = Fernet.generate_key()
with open("symmetric.key", "wb") as key_file:
    key_file.write(key)