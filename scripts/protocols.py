# Import standard Python libraries for file operations, system paths, and YAML parsing
import os  # For file and directory operations (e.g., path joining)
import sys  # For modifying sys.path to find local modules
import yaml  # For parsing the protocol_actions.yml file
import time  # For adding delays between operations

# Import Juniper PyEZ modules for interacting with Junos devices
from jnpr.junos.utils.config import Config  # Manages configuration changes on Junos devices

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
    username = input("Enter SSH username: ")  # Get username from user input
    password = input("Enter SSH password: ")  # Get password from user input
    connections = connect_to_hosts(username=username, password=password)  # Returns list of Device objects
    if not connections:  # Check if no connections were established
        print("No Device connected. Exiting ...")  # Inform user of failure
        disconnect_from_hosts(connections)  # Clean up any partial connections
        sys.exit(0)  # Exit script cleanly
    return connections  # Return the list of connected Device objects

def load_protocol_actions():
    """Load protocol actions from protocol_actions.yml"""
    file_path = os.path.join(SCRIPT_DIR, "../data/protocol_actions.yml")  # Construct path to YAML
    try:
        with open(file_path, 'r') as yaml_file:  # Open YAML file in read mode
            return yaml.safe_load(yaml_file)  # Parse and return YAML content as a dict
    except FileNotFoundError:  # Handle missing file
        print(f"Error: YAML file '{file_path}' not found.")  # Notify user
        return None  # Return None to indicate failure
    except yaml.YAMLError as error:  # Handle parsing errors
        print(f"Error parsing YAML: {error}")  # Print error details
        return None  # Return None to indicate failure

def backup_bgp_group(dev, group_name):
    """Check if BGP group exists and back up its config in set format if it does."""
    try:
        # Fetch current BGP group config in set format
        bgp_config = dev.rpc.get_config(filter_xml=f"<protocols><bgp><group><name>{group_name}</name></group></bgp></protocols>", format='set')
        # Check if config has content (group exists)
        if bgp_config.text.strip():  # Simplified check
            # Save to a set file in backups/
            backup_file = os.path.join(SCRIPT_DIR, f"../backups/bgp_group_{group_name}_{dev.hostname}_{int(time.time())}.set")
            os.makedirs(os.path.dirname(backup_file), exist_ok=True)  # Ensure backups/ exists
            with open(backup_file, 'w') as f:
                f.write(bgp_config.text.strip())  # Write set commands
            print(f"Backed up existing BGP group {group_name} to {backup_file}")
            return True  # Group exists
        print(f"No existing BGP group {group_name} found on {dev.hostname}")
        return False  # Group doesn’t exist
    except Exception as e:
        print(f"Error checking/backup for {group_name}: {e}")
        return False

def protocol_actions():
    """Main function to handle protocol actions."""
    connections = open_connections()  # Establish device connections
    actions = load_protocol_actions()  # Load YAML actions
    if actions and 'actions' in actions:  # Check if actions loaded successfully
        env = Environment(loader=FileSystemLoader(os.path.join(SCRIPT_DIR, '../templates')))  # Set up Jinja2 environment
        template = env.get_template('bgp_config.j2')  # Load BGP template
        for action_data in actions['actions']:  # Iterate over YAML actions
            if action_data['protocol'] == 'bgp':  # Filter for BGP actions
                # Render the config once (same for all devices)
                if action_data['action'] == 'add':
                    peers = list(zip(action_data['peer_ip'], action_data['peer_as']))  # Zip peers in Python
                    config = template.render(
                        action='add',
                        group_name=action_data['group_name'],
                        local_as=action_data['local_as'],
                        peers=peers,
                        advertised_subnet=action_data.get('advertised_subnet', []),
                        received_subnets=action_data.get('received_subnets', [])
                    )
                    print(f"BGP Config for {action_data['group_name']}:\n{config}")
                elif action_data['action'] == 'delete':
                    config = template.render(
                        action='delete',
                        group_name=action_data['group_name']
                    )
                    print(f"BGP Delete Config for {action_data['group_name']}:\n{config}")

                # Apply config to each connected device
                for dev in connections:
                    hostname = dev.facts.get('hostname', dev._hostname)  # Get device hostname or IP
                    print(f"\nApplying config to {hostname} ({dev._hostname})")
                    config_obj = Config(dev)  # Create Config object for this device
                    try:
                        config_obj.lock()  # Lock the config
                        # Check and backup existing group
                        group_exists = backup_bgp_group(dev, action_data['group_name'])
                        if group_exists and action_data['action'] == 'add':
                            config_obj.load(f"delete protocols bgp group {action_data['group_name']}", format='set')
                            config_obj.commit(timeout=30)  # Commit delete first
                            time.sleep(2)  # Small delay to ensure delete applies
                        # Load and apply new config
                        config_obj.load(config, format='set')
                        print(f"Configuration diff:\n{config_obj.diff() or 'No changes'}")
                        config_obj.commit(timeout=60)  # Commit new config
                        print(f"Successfully committed config to {hostname}")
                        time.sleep(5)  # Wait for routing subsystem to stabilize
                        # Verification commands with headers
                        try:
                            print("\n========== BGP SUMMARY ==========")
                            bgp_summary = dev.rpc.get_bgp_summary_information()
                            print(bgp_summary.text.strip() if bgp_summary.text else "No BGP summary available")
                        except Exception as e:
                            print(f"BGP Summary failed: {e}")

                        peer_ip = action_data['peer_ip'][0]  # Use first peer IP
                        try:
                            print("\n========== ADVERTISED SUBNETS ==========")
                            advertised = dev.rpc.get_route_information(protocol='bgp', active_path=True)
                            print(advertised.text.strip() if advertised.text else "No advertised routes")
                        except Exception as e:
                            print(f"Advertised Subnets failed: {e}")

                        try:
                            print("\n========== RECEIVED SUBNETS ==========")
                            received = dev.rpc.get_route_information(protocol='bgp')
                            print(received.text.strip() if received.text else "No received routes")
                        except Exception as e:
                            print(f"Received Subnets failed: {e}")
                    except Exception as e:
                        print(f"Failed to configure {hostname}: {e}")
                    finally:
                        if 'config_obj' in locals():
                            try:
                                config_obj.unlock()
                            except Exception:
                                pass
    disconnect_from_hosts(connections)  # Close all connections
    print("\nAll connections closed.")  # Confirm completion

protocol_actions()  # Run the main function
