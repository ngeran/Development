import os
import time
from datetime import datetime
from jnpr.junos.exception import ConnectError

def capture_routing_tables(device, host_name, routing_dir):
    """Capture routing tables and return them as a dict."""
    tables = {}
    try:
        # Capture each table specified in hosts_data.yml
        for table in device.tables:  # Assumes 'tables' is passed in hosts_data.yml
            route_info = device.rpc.cli(f"show route table {table}", format='text')
            tables[table] = route_info.text.strip()
        return tables
    except Exception as error:
        print(f"Failed to capture routing tables for {host_name} ({device.hostname}): {error}")
        return None

def save_routing_tables(tables, host_name, routing_dir, timestamp):
    """Save routing tables to files."""
    for table_name, table_content in tables.items():
        filename = f"{host_name}_{table_name}_{timestamp}.txt"
        filepath = os.path.join(routing_dir, filename)
        with open(filepath, 'w') as f:
            f.write(table_content)
        return filepath  # Return last filepath for reporting

def compare_tables(old_tables, new_tables):
    """Compare old and new routing tables, return changes."""
    changes = {}
    for table_name in old_tables:
        if table_name not in new_tables:
            changes[table_name] = "Table removed"
            continue
        old_lines = set(old_tables[table_name].splitlines())
        new_lines = set(new_tables[table_name].splitlines())
        additions = new_lines - old_lines
        subtractions = old_lines - new_lines
        if additions or subtractions:
            changes[table_name] = {
                'additions': list(additions),
                'subtractions': list(subtractions)
            }
    for table_name in new_tables:
        if table_name not in old_tables:
            changes[table_name] = "Table added"
    return changes

def route_monitor(username, password, host_ips, hosts, connect_to_hosts, disconnect_from_hosts, interval):
    """Monitor routing tables at specified intervals and report changes."""
    routing_dir = os.path.join(os.path.dirname(__file__), '../routing')
    os.makedirs(routing_dir, exist_ok=True)  # Create routing folder if missing
    report_dir = os.path.join(os.path.dirname(__file__), '../reports')
    os.makedirs(report_dir, exist_ok=True)  # Create reports folder if missing

    # Add tables to each host's data
    tables = hosts[0].get('tables', ['inet.0'])  # Assume tables are at top level for now
    for host in hosts:
        host['tables'] = tables

    connections = connect_to_hosts(username=username, password=password, host_ips=host_ips)
    if not connections:
        print("No devices connected for route monitoring.")
        return

    host_lookup = {h['ip_address']: h['host_name'] for h in hosts}
    previous_tables = {}  # Store previous captures

    print(f"Starting route monitoring with {interval}-second interval. Press Ctrl+C to stop.")
    try:
        while True:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report = f"Route Monitoring Report - {timestamp}\n{'='*50}\n"

            for dev in connections:
                host_name = host_lookup.get(dev.hostname, dev.hostname)
                dev.tables = tables  # Attach tables to device object
                new_tables = capture_routing_tables(dev, host_name, routing_dir)
                if not new_tables:
                    continue

                # Save new tables
                filepath = save_routing_tables(new_tables, host_name, routing_dir, timestamp)

                # Compare with previous tables
                if host_name in previous_tables:
                    changes = compare_tables(previous_tables[host_name], new_tables)
                    if changes:
                        report += f"\nChanges for {host_name} ({dev.hostname}):\n"
                        for table_name, change in changes.items():
                            report += f"  Table {table_name}:\n"
                            if isinstance(change, dict):
                                if change['additions']:
                                    report += f"    Additions:\n      - " + "\n      - ".join(change['additions']) + "\n"
                                if change['subtractions']:
                                    report += f"    Subtractions:\n      - " + "\n      - ".join(change['subtractions']) + "\n"
                            else:
                                report += f"    {change}\n"
                    else:
                        report += f"\nNo changes for {host_name} ({dev.hostname})\n"
                else:
                    report += f"\nInitial capture for {host_name} ({dev.hostname}) saved to {filepath}\n"

                previous_tables[host_name] = new_tables

            # Save report
            report_file = os.path.join(report_dir, f"route_report_{timestamp}.txt")
            with open(report_file, 'w') as f:
                f.write(report)
            print(f"\nReport generated: {report_file}")

            time.sleep(interval)

    except KeyboardInterrupt:
        print("\nRoute monitoring stopped by user.")
    finally:
        disconnect_from_hosts(connections)
