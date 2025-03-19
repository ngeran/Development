import os  # For file and directory operations
import sys  # For modifying sys.path to import connect_to_hosts
from datetime import datetime  # For generating timestamps in filenames
from jnpr.junos.utils.config import Config  # PyEZ Config class for managing configurations
from jnpr.junos import Device  # PyEZ Device class (already imported in connect_to_hosts)

# Adjust sys.path to include the scripts directory where connect_to_hosts.py resides
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # Directory of this script (scripts/)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)  # Add scripts/ to sys.path for importing

# Import connection functions from connect_to_hosts.py (in scripts/)
try:
    from connect_to_hosts import connect_to_hosts, disconnect_from_hosts
except ModuleNotFoundError as e:
    print(f"Error: Could not import connect_to_hosts: {e}")
    print(f"sys.path: {sys.path}")
    sys.exit(1)  # Exit if import fails

# Prompt user for SSH credentials (since this runs standalone from main.py)
username = input("Enter SSH username: ")
password = input("Enter SSH password: ")

# Connect to devices using connect_to_hosts from connect_to_hosts.py
connections = connect_to_hosts(username=username, password=password)

# Check if any connections were successful
if not connections:
    print("No devices connected. Exiting.")
    disconnect_from_hosts(connections)
    sys.exit(0)

# Define the backup directory in the root directory (one level up from scripts/)
backup_dir = os.path.join(os.path.dirname(SCRIPT_DIR), "backups")  # /home/nikos/Development/backups/

# Create the backups directory if it doesn’t exist
if not os.path.exists(backup_dir):
    os.makedirs(backup_dir)
    print(f"Created backup directory: {backup_dir}")

# Get current timestamp for unique filenames (e.g., 20250318_193828)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Iterate over each connected device to backup its configuration
for dev in connections:
    try:
        # Get the hostname from device facts (refreshed during connection)
        hostname = dev.facts.get('hostname', 'unknown_host')
        print(f"Backing up configuration for {hostname} ({dev._hostname})")

        # Create a Config object to access the device’s configuration
        config = Config(dev)

        # Lock the configuration to prevent changes during backup
        config.lock()

        # Get configuration in JSON format
        json_config = config.rpc.get_config(options={'format': 'json'})
        json_filename = os.path.join(backup_dir, f"{hostname}_{timestamp}.json")

        # Save JSON config to file
        with open(json_filename, 'w') as json_file:
            import json  # Local import for JSON serialization
            json.dump(json_config, json_file, indent=4)
        print(f"Saved JSON backup: {json_filename}")

        # Get configuration in set format
        set_config = config.rpc.get_config(options={'format': 'set'})
        set_filename = os.path.join(backup_dir, f"{hostname}_{timestamp}.set")

        # Save set config to file (set format is plain text)
        with open(set_filename, 'w') as set_file:
            set_file.write(set_config.text)
        print(f"Saved set backup: {set_filename}")

        # Unlock the configuration after backup (only once here)
        config.unlock()

    except Exception as e:
        print(f"Failed to backup {dev._hostname}: {e}")
        # If an error occurs before unlocking, attempt to unlock here
        try:
            if 'config' in locals():
                config.unlock()
        except Exception as unlock_error:
            print(f"Error unlocking config for {dev._hostname}: {unlock_error}")

# Always disconnect from devices after processing
disconnect_from_hosts(connections)
print("\nAll connections closed.")
