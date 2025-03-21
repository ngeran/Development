import os
import sys
import yaml

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

try:
    from connect_to_hosts import connect_to_hosts, disconnect_from_hosts
except ModuleNotFoundError as e:
    print(f"Error: Could not import connect_to_hosts: {e}")  # Fixed error message
    sys.exit(1)

def open_connections():
    """Open connections to devices and return the list of connections."""
    username = input("Enter SSH username: ")
    password = input("Enter SSH password: ")
    connections = connect_to_hosts(username=username, password=password)
    if not connections:
        print("No Device connected. Exiting ...")
        disconnect_from_hosts(connections)
        sys.exit(0)
    return connections

def load_protocol_actions():
    """Load protocol actions from protocol_actions.yml"""
    file_path = os.path.join(SCRIPT_DIR, "../data/protocol_actions.yml")
    try:
        with open(file_path, 'r') as yaml_file:
            return yaml.safe_load(yaml_file)
    except FileNotFoundError:
        print(f"Error: YAML file '{file_path}' not found.")
        return None
    except yaml.YAMLError as error:
        print(f"Error parsing YAML: {error}")
        return None

def protocol_actions():
    """Main function to handle protocol actions."""
    connections = open_connections()
    # Add menu logic here later
    disconnect_from_hosts(connections)
    print("\nAll connections closed.")
