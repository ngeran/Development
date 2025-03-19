import yaml  # For parsing the hosts.yml file
import os   # For handling file paths and directories
from jnpr.junos import Device  # PyEZ’s Device class for Junos device connections
from typing import List, Dict  # For type hints to improve code clarity

def load_hosts_from_yaml(file_path: str = "../data/hosts.yml") -> Dict:
    """Load host data from the YAML file.

    Args:
        file_path (str): Path to the hosts.yml file, relative to this script’s directory (scripts/).
                         Defaults to '../data/hosts.yml' to reach /data/ from /scripts/.

    Returns:
        dict: Parsed YAML data containing host information.

    Raises:
        FileNotFoundError: If the specified YAML file doesn’t exist.
    """
    # Get the directory of this script (connect_to_hosts.py), which is /home/nikos/Development/scripts/
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the full path to hosts.yml (e.g., /home/nikos/Development/data/hosts.yml)
    full_path = os.path.join(script_dir, file_path)

    # Check if the file exists; raise an error if it doesn’t
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Hosts file not found at {full_path}")

    # Open and parse the YAML file, returning its contents as a Python dict
    with open(full_path, 'r') as file:
        return yaml.safe_load(file)

def connect_to_hosts(username: str, password: str) -> List[Device]:
    """Connect to all Junos hosts listed in the YAML file.

    Args:
        username (str): SSH username for device authentication.
        password (str): SSH password for device authentication.

    Returns:
        list: List of PyEZ Device objects for successfully connected hosts.
    """
    # Load host data from hosts.yml
    host_data = load_hosts_from_yaml()
    connections = []  # Initialize an empty list to store Device objects

    # Check if host_data is valid and contains 'hosts' key
    if not host_data or 'hosts' not in host_data:
        print("No hosts found in YAML file.")
        return connections

    # Iterate over host types (routers and switches) in the YAML data
    for host_type in ['routers', 'switches']:
        if host_type in host_data['hosts']:
            # Iterate over each host in the current host_type
            for host in host_data['hosts'][host_type]:
                # Create a PyEZ Device object with host details
                dev = Device(
                    host=host['host_ip'],  # IP address from YAML
                    user=username,         # SSH username
                    password=password,     # SSH password
                    port=22                # Default SSH port
                )
                try:
                    # Attempt to open an SSH connection to the device
                    dev.open()
                    # Print success message with IP and hostname from YAML
                    print(f"Connected to {host['host_ip']} ({host['host_name']})")
                    connections.append(dev)  # Add connected device to the list
                except Exception as e:
                    # Print failure message if connection fails (e.g., timeout)
                    print(f"Failed to connect to {host['host_ip']} ({host['host_name']}): {e}")

    return connections

def disconnect_from_hosts(connections: List[Device]):
    """Close all connections to the hosts.

    Args:
        connections (list): List of PyEZ Device objects to disconnect.
    """
    # Iterate over each connected device
    for dev in connections:
        try:
            # Close the SSH connection to the device
            dev.close()
            # Print confirmation using device hostname and IP
            print(f"Disconnected from {dev.hostname} ({dev._hostname})")
        except Exception as e:
            # Print error if disconnection fails (e.g., already closed)
            print(f"Error disconnecting from {dev._hostname}: {e}")

if __name__ == "__main__":
    # Example usage: connect with test credentials and disconnect
    connections = connect_to_hosts(username="admin", password="your_password")
    disconnect_from_hosts(connections)
