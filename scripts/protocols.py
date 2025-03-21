# Import standard Python libraries for file operations, system paths, and YAML parsing
import os  # For file and directory operations (e.g., path joining)
import sys  # For modifying sys.path to find local modules
import yaml  # For parsing the protocol_actions.yml file

# Import Juniper PyEZ modules for interacting with Junos devices

# Import Jinja2 for templating configuration commands
from jinja2 import Environment, FileSystemLoader  # Environment for rendering templates, FileSystemLoader for loading them from disk

# Define the directory where this script lives (scripts/)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # Get absolute path of current script's directory
if SCRIPT_DIR not in sys.path:  # Check if scripts/ is in Python's module search path
    sys.path.insert(0, SCRIPT_DIR)  # Add scripts/ to the start of sys.path for importing local modules

# Attempt to import connection functions from connect_to_hosts.py
try:
    from connect_to_hosts import connect_to_hosts, disconnect_from_hosts  # Functions to connect/disconnect from devices
except ModuleNotFoundError as e:  # Catch if connect_to_hosts.py is missing
    print(f"Error: Could not import connect_to_hosts: {e}")  # Print error message with exception details
    sys.exit(1)  # Exit the script with an error code (1 indicates failure)

def open_connections():
    """Open connections to devices and return the list of connections."""
    # Prompt user for SSH credentials to connect to devices
    username = input("Enter SSH username: ")  # Get username from user input
    password = input("Enter SSH password: ")  # Get password from user input (note: not secure for production—consider getpass)
    # Attempt to connect to hosts defined in hosts.yml using credentials
    connections = connect_to_hosts(username=username, password=password)  # Returns list of Device objects
    if not connections:  # Check if no connections were established
        print("No Device connected. Exiting ...")  # Inform user of failure
        disconnect_from_hosts(connections)  # Clean up any partial connections (likely empty here)
        sys.exit(0)  # Exit script cleanly (0 indicates success, though could use 1 for failure)
    return connections  # Return the list of connected Device objects

def load_protocol_actions():
    """Load protocol actions from protocol_actions.yml"""
    # Construct the full path to protocol_actions.yml (relative to scripts/, up to data/)
    file_path = os.path.join(SCRIPT_DIR, "../data/protocol_actions.yml")
    try:
        with open(file_path, 'r') as yaml_file:  # Open the YAML file in read mode
            return yaml.safe_load(yaml_file)  # Parse YAML content into a Python dict and return it
    except FileNotFoundError:  # Handle case where the file doesn’t exist
        print(f"Error: YAML file '{file_path}' not found.")  # Notify user of missing file
        return None  # Return None to indicate failure
    except yaml.YAMLError as error:  # Handle YAML parsing errors (e.g., syntax issues)
        print(f"Error parsing YAML: {error}")  # Print parsing error details
        return None  # Return None to indicate failure

def protocol_actions():
    """Main function to handle protocol actions."""
    # Establish connections to devices
    connections = open_connections()  # Get list of Device objects from open_connections()
    # Load protocol actions from YAML file
    actions = load_protocol_actions()  # Get dict from protocol_actions.yml or None if failed
    # Check if actions were loaded succesfully and contain the 'actions' KeyboardInterrupt
    if actions and 'actions' in actions: # Ensure actions is not None and has the expected structure
        # Setup Jinja2 enviorment to load templates from the templates/ directory
        env = Environment(loader=FileSystemLoader(os.path.join(SCRIPT_DIR, '../templates')))
        # Load the bgp configurarion templates
        template = env.get_template('bgp_config.j2')


        # Iterate over each action defined in the YAML
        for action_data in actions['actions']: # Loop through list under 'actions' Key
            # Check if the protocol is 'bgp'
            if action_data['protocol'] == 'bgp': # Filter for bgp specific actions
                # Add actions
                if action_data['action'] == 'add':
                    # Render Jinja2 with the BGP configuration
                    config = template.render(
                        action = 'add',
                        group_name = action_data['group_name'],
                        local_as=action_data['local_as'],
                        peer_as=action_data['peer_as'],
                        peer_ip=action_data['peer_ip'],
                        # Use .get() to provide empty list if key is missing, ensuring reject policy-options
                        advertised_subnet=action_data.get('advertised_subnet', []),
                        received_subnet=action_data.get('received_subnet', [])
                    )
                    # Print the rendered BGP configuration for review
                    print(f"BGP Config for {action_data['group_name']}:\n{config}")
                # Handle 'delete' action to remove BGP configuration
                elif action_data['action'] == 'delete':
                    # Render the Jinja2 template with BGP config
                    config = template.render(
                        action = 'delete',
                        group_name = action_data['group_name']
                    )
                    # Print the rendered delete configuration for review
                    print(f"BGP Delete Config for {action_data['group_name']}:\n{config}")
            # Placeholder for future OSPF logic (not implemented yet)
            # OSPF to be added later

    # Add menu logic here later
    disconnect_from_hosts(connections)
    print("\nAll connections c hlosed.")

protocol_actions()
