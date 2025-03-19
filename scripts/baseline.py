import os  # For file and directory operations
import sys  # For modifying sys.path to import connect_to_hosts
from datetime import datetime  # For generating timestamps in filenames
from jnpr.junos import Device  # PyEZ Device class for Junos connections
import json  # For saving baseline data in JSON format
import yaml  # For saving baseline data in YAML format

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

def general_info(dev: Device) -> dict:
    """Collect general device information including facts, routing table, environmental, power, and transceivers.

    Args:
        dev (Device): PyEZ Device object for the connected device.
    Returns:
        dict: General device information.
    """
    general_data = {}
    try:
        # Device Facts (hostname, model, etc.)
        dev.facts_refresh()  # Ensure facts are up-to-date
        general_data['facts'] = {
            'hostname': dev.facts.get('hostname', 'unknown_host'),
            'model': dev.facts.get('model', 'Unknown'),
            'version': dev.facts.get('version', 'Unknown'),
            'serial_number': dev.facts.get('serialnumber', 'Unknown')
        }

        # Routing Table (inet.0, IPv4)
        routes = dev.rpc.get_route_information(table="inet.0")
        general_data['routing_table'] = [
            {
                "destination": route.xpath('rt-destination')[0].text,
                "protocol": route.xpath('rt-entry/protocol-name')[0].text,
                "next_hop": route.xpath('rt-entry/nh/to')[0].text if route.xpath('rt-entry/nh/to') else "N/A"
            }
            for route in routes.xpath('route-table/rt')
        ]

        # Environmental (temperature, CPU load)
        env_info = dev.rpc.get_environment_information()
        general_data['environmental'] = {
            "temperature": env_info.xpath('//temperature')[0].text.strip() if env_info.xpath('//temperature') else "N/A",
            "cpu_load": env_info.xpath('//cpu-load')[0].text.strip() if env_info.xpath('//cpu-load') else "N/A"
        }

        # Power Supply Status
        power_info = dev.rpc.get_power_information() if hasattr(dev.rpc, 'get_power_information') else None
        general_data['power'] = [
            {
                "name": ps.xpath('name')[0].text,
                "status": ps.xpath('state')[0].text
            }
            for ps in power_info.xpath('power-supply') if power_info
        ] if power_info else "No power supply info"

        # Transceiver Information
        transceivers = dev.rpc.get_interface_optics_diagnostics_information()
        general_data['transceivers'] = [
            {
                "interface": xcvr.xpath('name')[0].text,
                "rx_power_dbm": xcvr.xpath('optics-diagnostics/lane-optics-diagnostic/rx-power')[0].text if xcvr.xpath('optics-diagnostics/lane-optics-diagnostic/rx-power') else "N/A",
                "tx_power_dbm": xcvr.xpath('optics-diagnostics/lane-optics-diagnostic/tx-power')[0].text if xcvr.xpath('optics-diagnostics/lane-optics-diagnostic/tx-power') else "N/A"
            }
            for xcvr in transceivers.xpath('physical-interface')
        ] if transceivers.xpath('physical-interface') else "No transceivers"

    except Exception as e:
        print(f"Failed to collect general info for {dev._hostname}: {e}")
        general_data['error'] = str(e)

    return general_data

def ospf(dev: Device) -> dict:
    """Collect OSPF-related information including interfaces and neighbors.

    Args:
        dev (Device): PyEZ Device object for the connected device.
    Returns:
        dict: OSPF information.
    """
    ospf_data = {}
    try:
        # OSPF Interfaces
        ospf_interfaces = dev.rpc.get_ospf_interface_information()
        ospf_data['interfaces'] = [
            {
                "interface_name": intf.xpath('interface-name')[0].text,
                "area": intf.xpath('ospf-area')[0].text,
                "state": intf.xpath('ospf-interface-state')[0].text
            }
            for intf in ospf_interfaces.xpath('ospf-interface')
        ] if ospf_interfaces.xpath('ospf-interface') else "No OSPF interfaces"

        # OSPF Neighbors
        ospf_neighbors = dev.rpc.get_ospf_neighbor_information()
        ospf_data['neighbors'] = [
            {
                "neighbor_address": neigh.xpath('neighbor-address')[0].text,
                "interface": neigh.xpath('interface-name')[0].text,
                "state": neigh.xpath('ospf-neighbor-state')[0].text
            }
            for neigh in ospf_neighbors.xpath('ospf-neighbor')
        ] if ospf_neighbors.xpath('ospf-neighbor') else "No OSPF neighbors"

    except Exception as e:
        print(f"Failed to collect OSPF data for {dev._hostname}: {e}")
        ospf_data['error'] = str(e)

    return ospf_data

def bgp(dev: Device) -> dict:
    """Collect BGP summary information.

    Args:
        dev (Device): PyEZ Device object for the connected device.
    Returns:
        dict: BGP summary information.
    """
    bgp_data = {}
    try:
        # BGP Summary
        bgp_summary = dev.rpc.get_bgp_summary_information()
        bgp_data['summary'] = [
            {
                "peer_address": peer.xpath('peer-address')[0].text,
                "peer_as": peer.xpath('peer-as')[0].text,
                "state": peer.xpath('peer-state')[0].text,
                "up_time": peer.xpath('elapsed-time')[0].text if peer.xpath('elapsed-time') else "N/A"
            }
            for peer in bgp_summary.xpath('bgp-peer')
        ] if bgp_summary.xpath('bgp-peer') else "No BGP peers"

    except Exception as e:
        print(f"Failed to collect BGP data for {dev._hostname}: {e}")
        bgp_data['error'] = str(e)

    return bgp_data

def interfaces(dev: Device) -> dict:
    """Collect interface descriptions.

    Args:
        dev (Device): PyEZ Device object for the connected device.
    Returns:
        dict: Interface descriptions.
    """
    interface_data = {}
    try:
        interfaces = dev.rpc.get_interface_information(descriptions=True, terse=True)
        interface_data['descriptions'] = {
            interface.xpath('name')[0].text: interface.xpath('description')[0].text
            if interface.xpath('description') else "No description"
            for interface in interfaces.xpath('physical-interface')
        }
    except Exception as e:
        print(f"Failed to collect interface data for {dev._hostname}: {e}")
        interface_data['error'] = str(e)

    return interface_data

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

# Define the baseline directory in the root directory (one level up from scripts/)
baseline_dir = os.path.join(os.path.dirname(SCRIPT_DIR), "baselines")  # /home/nikos/Development/baselines/

# Create the baselines directory if it doesn’t exist
if not os.path.exists(baseline_dir):
    os.makedirs(baseline_dir)
    print(f"Created baseline directory: {baseline_dir}")

# Get current timestamp for unique filenames (e.g., 20250318_193828)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Iterate over each connected device to collect baseline information
for dev in connections:
    try:
        # Get the hostname from device facts
        hostname = dev.facts.get('hostname', 'unknown_host')
        print(f"Collecting baseline for {hostname} ({dev._hostname})")

        # Create a device-specific subfolder inside baselines/
        device_dir = os.path.join(baseline_dir, hostname)
        if not os.path.exists(device_dir):
            os.makedirs(device_dir)
            print(f"Created device directory: {device_dir}")

        # Collect all baseline data using separate functions
        baseline_data = {
            "general_info": general_info(dev),
            "ospf": ospf(dev),
            "bgp": bgp(dev),
            "interfaces": interfaces(dev)
        }

        # Base filename without extension
        base_filename = os.path.join(device_dir, f"{hostname}_{timestamp}_baseline")

        # Save as JSON
        json_filename = f"{base_filename}.json"
        with open(json_filename, 'w') as json_file:
            json.dump(baseline_data, json_file, indent=4)
        print(f"Saved JSON baseline: {json_filename}")

        # Save as YAML
        yaml_filename = f"{base_filename}.yml"
        with open(yaml_filename, 'w') as yaml_file:
            yaml.safe_dump(baseline_data, yaml_file, default_flow_style=False)
        print(f"Saved YAML baseline: {yaml_filename}")

        # Save as TXT (human-readable format)
        txt_filename = f"{base_filename}.txt"
        with open(txt_filename, 'w') as txt_file:
            txt_file.write(f"Baseline for {hostname} ({dev._hostname})\n")
            txt_file.write("=" * 50 + "\n\n")

            # General Info
            txt_file.write("General Information:\n")
            txt_file.write("-" * 20 + "\n")
            for key, value in baseline_data['general_info'].items():
                txt_file.write(f"{key.replace('_', ' ').title()}:\n")
                if isinstance(value, dict):
                    for subkey, subval in value.items():
                        txt_file.write(f"  {subkey}: {subval}\n")
                elif isinstance(value, list):
                    for item in value:
                        txt_file.write(f"  - {item}\n")
                else:
                    txt_file.write(f"  {value}\n")
            txt_file.write("\n")

            # OSPF
            txt_file.write("OSPF Information:\n")
            txt_file.write("-" * 20 + "\n")
            for key, value in baseline_data['ospf'].items():
                txt_file.write(f"{key.title()}:\n")
                if isinstance(value, list):
                    for item in value:
                        txt_file.write(f"  - {item}\n")
                else:
                    txt_file.write(f"  {value}\n")
            txt_file.write("\n")

            # BGP
            txt_file.write("BGP Information:\n")
            txt_file.write("-" * 20 + "\n")
            for key, value in baseline_data['bgp'].items():
                txt_file.write(f"{key.title()}:\n")
                if isinstance(value, list):
                    for item in value:
                        txt_file.write(f"  - {item}\n")
                else:
                    txt_file.write(f"  {value}\n")
            txt_file.write("\n")

            # Interfaces
            txt_file.write("Interfaces:\n")
            txt_file.write("-" * 20 + "\n")
            for key, value in baseline_data['interfaces'].items():
                txt_file.write(f"{key.title()}:\n")
                if isinstance(value, dict):
                    for intf, desc in value.items():
                        txt_file.write(f"  {intf}: {desc}\n")
                else:
                    txt_file.write(f"  {value}\n")
        print(f"Saved TXT baseline: {txt_filename}")

    except Exception as e:
        print(f"Failed to process {dev._hostname}: {e}")

# Always disconnect from devices after processing
disconnect_from_hosts(connections)
print("\nAll connections closed.")
