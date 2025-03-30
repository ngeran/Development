from jnpr.junos import Device  # PyEZ’s Device class for Junos device connections
from typing import List  # For type hints to improve code clarity

def connect_to_hosts(username: str, password: str, host_ips: List[str]) -> List[Device]:
    """Connect to all Junos hosts listed in the provided list of host IPs.

    Args:
        username (str): SSH username for device authentication.
        password (str): SSH password for device authentication.
        host_ips (list): List of host IPs to connect to.

    Returns:
        list: List of PyEZ Device objects for successfully connected hosts.
    """
    # Initialize an empty list to store Device objects
    connections = []

    # Iterate over host ips in the provides list
    for host_ip in host_ips:
        try:
            # Create a PyEZ with host_ip and authentication details
            dev = Device(
                # Host IP address provided from the list
                host=host_ip,
                # SSH username
                user=username,
                # SSH password
                password=password,
                # Default SSH port
                port=22
            )

            # Attempt to open an SSH connection to the device
            dev.open()
            # Print success message with the host IP
            print(f"Connected to {host_ip}")
            # Add connected device to the list
            connections.append(dev)
        except Exception as error:
            # Print failure message if connection fails (e.g., timeout, authentication error)
            print(f"Failed to connect to {host_ip}: {error}")
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
