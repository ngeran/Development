import os  # For handling file paths and directories
import sys  # For modifying Python's module search path (sys.path)

# Define the directory where this script (get_device_facts.py) resides
# os.path.abspath(__file__) gives the full path to this file
# os.path.dirname(...) extracts just the directory part
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
#print(f"Script directory: {SCRIPT_DIR}")  # Debug: Show where the script is running from
#print(f"Current sys.path: {sys.path}")  # Debug: Show Python's module search path

# Add SCRIPT_DIR to sys.path if it's not already there
# This ensures Python can find connect_to_hosts.py in the same directory
# sys.path.insert(0, ...) puts it at the start for priority
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
    #print(f"Added {SCRIPT_DIR} to sys.path")  # Debug: Confirm path addition

# Attempt to import functions from connect_to_hosts.py
# Wrapped in try/except to catch and debug import errors
try:
    from connect_to_hosts import connect_to_hosts, disconnect_from_hosts
except ModuleNotFoundError as e:
    print(f"Error: {e}")  # Print the import error (e.g., module not found)
    print(f"sys.path after adjustment: {sys.path}")  # Show final sys.path for debugging
    sys.exit(1)  # Exit with an error code if import fails

def get_device_facts(connections: list) -> dict:
    """Collect facts from each connected Junos device using PyEZ.

    Args:
        connections (list): List of PyEZ Device objects representing connected hosts.

    Returns:
        dict: A dictionary mapping device IP addresses to their facts or errors.
    """
    device_facts = {}  # Initialize an empty dict to store facts for each device

    # Iterate over each connected device
    for dev in connections:
        try:
            # Refresh the device's facts to ensure they’re up-to-date
            # PyEZ populates dev.facts with device info after this call
            dev.facts_refresh()

            # Extract key facts from dev.facts, with defaults if not available
            facts = {
                'hostname': dev.facts.get('hostname', 'Unknown'),  # Device hostname
                'model': dev.facts.get('model', 'Unknown'),        # Device model (e.g., SRX320)
                'version': dev.facts.get('version', 'Unknown'),    # Junos OS version
                'serial_number': dev.facts.get('serialnumber', 'Unknown')  # Serial number
            }
            # Store facts using the device’s IP address (dev._hostname) as the key
            device_facts[dev._hostname] = facts
        except Exception as e:
            # If fact collection fails (e.g., connection lost), log the error
            print(f"Failed to collect facts from {dev._hostname}: {e}")
            device_facts[dev._hostname] = {'error': str(e)}  # Store the error in the dict

    return device_facts  # Return the collected facts

def main():
    """Main function to orchestrate device connection and fact collection."""
    # Use try/except to handle runtime errors and user interruptions
    try:
        # Prompt user for SSH credentials to connect to devices
        username = input("Enter SSH username: ")
        password = input("Enter SSH password: ")

        # Connect to all hosts listed in data/hosts.yml using credentials
        # connect_to_hosts() returns a list of PyEZ Device objects
        connections = connect_to_hosts(username=username, password=password)

        # If no connections were successful, exit early
        if not connections:
            print("No successful connections established.")
            return

        # Collect facts from all connected devices
        facts = get_device_facts(connections)

        # Display the collected facts in a readable format
        print("\nCollected Device Facts:")
        print("-----------------------")
        for ip, info in facts.items():
            print(f"Device {ip}:")  # IP address as the device identifier
            if 'error' in info:
                print(f"  Error: {info['error']}")  # Show error if fact collection failed
            else:
                # Print each fact if available
                print(f"  Hostname: {info['hostname']}")
                print(f"  Model: {info['model']}")
                print(f"  Version: {info['version']}")
                print(f"  Serial Number: {info['serial_number']}")

    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully with a clean exit message
        print("\nScript terminated by user (Ctrl+C). Exiting gracefully.")
        sys.exit(0)  # Exit with success status (0)
    except Exception as e:
        # Catch any other runtime errors (e.g., network issues)
        print(f"An error occurred: {e}")
    finally:
        # Always disconnect from all devices, even if an error occurs
        disconnect_from_hosts(connections)
        print("\nAll connections closed.")  # Confirm cleanup

# Standard Python idiom to run main() if this script is executed directly
if __name__ == "__main__":
    main()
