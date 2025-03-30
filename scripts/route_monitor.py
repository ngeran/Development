# Import standard Python libraries for file operations, system paths, timing, YAML parsing, and date formatting
import os  # For file and directory operations (e.g., path joining)
import sys  # For modifying sys.path and exiting the script
import time  # For adding a delay between route table captures
import yaml  # For parsing the hosts.yml file
from datetime import datetime  # For timestamping log entries
from jnpr.junos.exception import RpcError  # Exception class for Junos RPC errors

# Define the directory where this script lives (scripts/)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # Get absolute path of current script's directory

# Add SCRIPT_DIR to sys.path if not already present, so we can import local modules
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)  # Insert at the start of sys.path for priority

# Attempt to import connection functions from connect_to_hosts.py
try:
    from connect_to_hosts import connect_to_hosts, disconnect_from_hosts  # Functions to connect/disconnect from devices
except ModuleNotFoundError as e:  # Catch if connect_to_hosts.py is missing
    print(f"Error: Could not import connect_to_hosts: {e}")  # Print error message with exception details
    sys.exit(1)  # Exit with an error code (1 indicates failure)

def load_hosts():
    """Load hosts, credentials, tables, and monitor interval from hosts.yml."""
    file_path = os.path.join(SCRIPT_DIR, "../data/hosts.yml")  # Construct path to hosts.yml in data/
    try:
        with open(file_path, 'r') as f:  # Open the YAML file in read mode
            return yaml.safe_load(f)  # Parse and return the full YAML content as a dict
    except Exception as e:  # Catch any errors (e.g., file not found, invalid YAML)
        print(f"Error loading hosts.yml: {e}")  # Print the error
        return {}  # Return empty dict to indicate failure

def get_routing_table(dev, tables):
    """Fetch specified routing tables from a device using 'show route terse'."""
    all_routes = {}  # Dict to store routes: {table: {prefix: {protocol, next_hop}}}

    for table in tables:  # Iterate over user-specified tables from hosts.yml
        try:
            # Fetch routes for the specified table in terse format
            route_output = dev.rpc.get_route_information(table=table, terse=True)
            routes = {}  # Dict for this table’s routes
            if hasattr(route_output, 'text') and route_output.text:  # Check if RPC returned text output
                for line in route_output.text.strip().splitlines():  # Split output into lines
                    if line.startswith((f'{table}:', '+', '=')):  # Skip table headers and diff markers
                        continue
                    parts = line.split()  # Split line into space-separated parts
                    if len(parts) >= 5:  # Ensure line has enough parts for a valid route
                        prefix = parts[1]  # Second column is the prefix (e.g., 10.0.1.0/24 or MPLS label)
                        protocol = parts[2].strip('[]').split('/')[0]  # Third column is protocol (e.g., BGP/170 -> BGP)
                        next_hop = parts[4] if parts[4].startswith('>') else ' '.join(parts[4:])  # Next hop or action
                        routes[prefix] = {'protocol': protocol, 'next_hop': next_hop}  # Store route details
            all_routes[table] = routes  # Add this table’s routes to the master dict
        except RpcError as e:  # Catch RPC errors (e.g., table doesn’t exist or device issue)
            print(f"Error fetching {table} from {dev.hostname}: {e}")  # Print error with table and hostname
            all_routes[table] = {}  # Assign empty dict for this table on failure

    return all_routes  # Return routes for all specified tables

def compare_routes(initial, updated):
    """Compare initial and updated routing tables, grouping changes by table and protocol."""
    changes = {'new': {}, 'updated': {}, 'removed': {}}  # Nested dict: {type: {table: {protocol: [changes]}}}

    # Initialize nested structure for each change type and table
    for change_type in changes:
        changes[change_type] = {table: {} for table in initial}

    # Compare each table
    for table in initial:
        # New prefixes (in updated but not initial)
        for prefix in updated[table]:
            if prefix not in initial[table]:
                protocol = updated[table][prefix]['protocol']  # Get protocol of new route
                if protocol not in changes['new'][table]:  # Initialize protocol list if not present
                    changes['new'][table][protocol] = []
                changes['new'][table][protocol].append({'prefix': prefix, 'details': updated[table][prefix]})

        # Removed prefixes (in initial but not updated)
        for prefix in initial[table]:
            if prefix not in updated[table]:
                protocol = initial[table][prefix]['protocol']  # Get protocol of removed route
                if protocol not in changes['removed'][table]:  # Initialize protocol list if not present
                    changes['removed'][table][protocol] = []
                changes['removed'][table][protocol].append({'prefix': prefix, 'details': initial[table][prefix]})

        # Updated prefixes (in both, but details changed)
        for prefix in initial[table]:
            if prefix in updated[table] and initial[table][prefix] != updated[table][prefix]:
                protocol = updated[table][prefix]['protocol']  # Use new protocol if it changed
                if protocol not in changes['updated'][table]:  # Initialize protocol list if not present
                    changes['updated'][table][protocol] = []
                changes['updated'][table][protocol].append({
                    'prefix': prefix,
                    'old': initial[table][prefix],
                    'new': updated[table][prefix]
                })

    return changes  # Return the structured changes

def log_changes(changes, dev_info, log_file):
    """Log only prefix changes to a file with table and protocol breakdown."""
    # Check if there are any changes to log
    has_changes = any(any(protos) for protos in changes['new'].values()) or \
                  any(any(protos) for protos in changes['updated'].values()) or \
                  any(any(protos) for protos in changes['removed'].values())

    if not has_changes:  # Skip logging if no changes
        return

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Format current time for log entry
    with open(log_file, 'a') as f:  # Open log file in append mode
        f.write(f"\n=== Route Changes at {timestamp} ===\n")  # Write timestamp header
        f.write(f"Device: {dev_info['host_name']} ({dev_info['host_ip']})\n")  # Write device hostname and IP
        f.write(f"Location: {dev_info['host_location']}, Function: {dev_info['function']}, Product: {dev_info['product_family']}\n")  # Write device categorization

        # Iterate over each table for all change types
        for table in changes['new']:
            # New prefixes by protocol for this table
            if changes['new'][table]:
                f.write(f"\nNew Prefixes in {table}:\n")  # Table-specific header
                for protocol, prefixes in changes['new'][table].items():  # Iterate over protocols
                    f.write(f"  {protocol}: {len(prefixes)} subnets changed\n")  # Write count of changed subnets
                    for change in prefixes:  # List each new prefix
                        f.write(f"    {change['prefix']} - {change['details']}\n")  # Write prefix and details

            # Updated prefixes by protocol for this table
            if changes['updated'][table]:
                f.write(f"\nUpdated Prefixes in {table}:\n")  # Table-specific header
                for protocol, prefixes in changes['updated'][table].items():  # Iterate over protocols
                    f.write(f"  {protocol}: {len(prefixes)} subnets changed\n")  # Write count of changed subnets
                    for change in prefixes:  # List each updated prefix
                        f.write(f"    {change['prefix']} - Old: {change['old']} | New: {change['new']}\n")  # Write old vs new

            # Removed prefixes by protocol for this table
            if changes['removed'][table]:
                f.write(f"\nRemoved Prefixes in {table}:\n")  # Table-specific header
                for protocol, prefixes in changes['removed'][table].items():  # Iterate over protocols
        f.write(f"  {protocol}: {len(prefixes)} subnets changed\n")  # Write count of changed subnets
                    for change in prefixes:  # List each removed prefix
                        f.write(f"    {change['prefix']} - {change['details']}\n")  # Write prefix and details

def monitor_routes():
    """Monitor routing tables continuously, logging changes based on user-defined interval until interrupted."""
    # Load hosts, credentials, tables, and monitor interval from hosts.yml
    config = load_hosts()  # Get the full YAML config (username, password, tables, monitor_interval, hosts)
    if not config or 'hosts' not in config:  # Check if config loaded and has hosts
        print("No hosts loaded. Exiting.")  # Print error if YAML is empty or invalid
        sys.exit(1)  # Exit with error

    # Extract global credentials, tables, and monitor interval with defaults if not present
    username = config.get('username', 'admin')  # Get username from YAML, default to 'admin'
    password = config.get('password', 'manolis1')  # Get password from YAML, default to 'manolis1'
    tables = config.get('tables', ['inet.0'])  # Get tables from YAML, default to ['inet.0'] if missing
    monitor_interval = config.get('monitor_interval', 1800)  # Get interval in seconds, default to 1800 (30 min)

    # Flatten the nested hosts structure (routers and switches) into a single list
    hosts = []  # List to hold all devices
    for category in ['routers', 'switches']:  # Iterate over host categories
        if category in config['hosts']:  # Check if category exists in hosts
            hosts.extend(config['hosts'][category])  # Add all devices from this category to the list

    if not hosts:  # Check if any hosts were found
        print("No devices found in hosts.yml. Exiting.")  # Print error if no devices are listed
        sys.exit(1)  # Exit with error

    # Connect to all devices using credentials
    connections = connect_to_hosts(username=username, password=password)  # Establish SSH connections
    if not connections:  # Check if any connections were successful
        print("No devices connected. Exiting.")  # Print error if:q no devices are reachable
        sys.exit(0)  # Exit cleanly

    # Capture initial routing tables for all devices
    initial_tables = {}  # Dict to store baseline tables: {hostname: {table: {prefix: {protocol, next_hop}}}}
    for dev in connections:  # Iterate over connected devices
        hostname = dev.facts.get('hostname', dev._hostname)  # Get hostname or fallback to IP
        initial_tables[hostname] = get_routing_table(dev, tables)  # Store initial tables for specified tables

    print(f"Initial routing tables captured for {tables}. Monitoring every {monitor_interval} seconds (Ctrl+C to stop)...")  # Inform user

    # Prepare log file path and ensure directory exists
    log_file = os.path.join(SCRIPT_DIR, "../logs/route_changes.log")  # Path to log file
    os.makedirs(os.path.dirname(log_file), exist_ok=True)  # Create logs/ directory if it doesn’t exist

    # Continuous monitoring loop with graceful exit
    try:
        while True:  # Run indefinitely until interrupted
            time.sleep(monitor_interval)  # Wait for user-defined interval
            for dev in connections:  # Iterate over connected devices
                hostname = dev.facts.get('hostname', dev._hostname)  # Get hostname or IP
                updated_table = get_routing_table(dev, tables)  # Fetch current tables
                changes = compare_routes(initial_tables[hostname], updated_table)  # Compare with baseline
                dev_info = next((h for h in hosts if h['host_name'] == hostname), {})  # Find device info
                log_changes(changes, dev_info, log_file)  # Log only if changes exist
                if any(any(protos) for protos in changes['new'].values()) or \
                   any(any(protos) for protos in changes['updated'].values()) or \
                   any(any(protos) for protos in changes['removed'].values()):
                    print(f"Changes detected for {hostname} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}, logged to {log_file}")
                initial_tables[hostname] = updated_table  # Update baseline for next cycle

    except KeyboardInterrupt:  # Catch Ctrl+C
        print("\nMonitoring stopped by user (Ctrl+C). Cleaning up...")  # Notify user
        disconnect_from_hosts(connections)  # Close all SSH sessions
        print("Connections closed. Exiting gracefully. Check route_changes.log for details.")  # Final message
        sys.exit(0)  # Exit cleanly

# Run the script if executed directly
if __name__ == "__main__":
    monitor_routes()  # Call the main function
