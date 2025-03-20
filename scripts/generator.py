import os  # For file and directory operations
import sys  # For modifying sys.path to import connect_to_hosts
from jnpr.junos.utils.config import Config  # PyEZ Config class for managing configurations

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

# Process each connected device to generate and apply configuration
for dev in connections:
    try:
        # Get the hostname from device facts (refreshed during connection)
        hostname = dev.facts.get('hostname', 'unknown_host')
        print(f"Processing {hostname} ({dev._hostname})")

        # Create a Config object to manage the device’s configuration
        config = Config(dev)

        # Lock the configuration to prevent changes during modification
        config.lock()

        # Generate a simple configuration (example: set hostname)
        new_hostname = f"{hostname}-updated"  # Example modification
        config_data = f"set system host-name {new_hostname}"

        # Load the configuration in set format
        config.load(config_data, format='set', overwrite=False)

        # Check for differences and commit if changes exist
        if config.diff():
            print(f"Configuration diff for {hostname}:\n{config.diff()}")
            config.commit(comment="Updated hostname via generator.py")
            print(f"Configuration applied to {hostname}")
        else:
            print(f"No changes needed for {hostname}")

        # Unlock the configuration after applying changes
        config.unlock()

    except Exception as e:
        print(f"Failed to process {dev._hostname}: {e}")
        # Ensure config is unlocked if an error occurs
        try:
            if 'config' in locals():
                config.unlock()
        except Exception as unlock_error:
            print(f"Error unlocking config for {dev._hostname}: {unlock_error}")

# Always disconnect from devices after processing
disconnect_from_hosts(connections)
print("\nAll connections closed.")
