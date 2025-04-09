import os
import argparse
from utils import merge_host_data
from connect_to_hosts import connect_to_hosts, disconnect_from_hosts

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    """Parse arguments and execute specified actions."""
    parser = argparse.ArgumentParser(description='Network device configuration script')
    parser.add_argument('--actions', nargs='+',
                        choices=['interfaces', 'bgp', 'ospf', 'ldp', 'rsvp', 'mpls',
                                 'ping', 'bgp_verification', 'ospf_verification',
                                 'backup', 'baseline', 'route_monitor'],
                        help='Actions to perform')
    args = parser.parse_args()

    inventory_file = os.path.join(SCRIPT_DIR, "../data/inventory.yml")
    config_file = os.path.join(SCRIPT_DIR, "../data/hosts_data.yml")

    merged_data = merge_host_data(inventory_file, config_file)
    if not merged_data:
        print("Failed to merge host data. Exiting.")
        return

    username = merged_data.get('username')
    password = merged_data.get('password')
    hosts = merged_data.get('hosts', [])
    host_ips = [host['ip_address'] for host in hosts]
    interval = merged_data.get('interval', 300)  # Default to 300s if missing

    # Configuration actions
    if 'interfaces' in args.actions:
        from interface_actions import configure_interfaces
        configure_interfaces(
            username=username,
            password=password,
            host_ips=host_ips,
            hosts=hosts,
            template_name='interface_template.j2',
            connect_to_hosts=connect_to_hosts,
            disconnect_from_hosts=disconnect_from_hosts
        )
    if any(action in ['bgp', 'ospf', 'ldp', 'rsvp', 'mpls'] for action in args.actions):
        from routing_protocols import configure_routing
        protocols = [action for action in args.actions if action in ['bgp', 'ospf', 'ldp', 'rsvp', 'mpls']]
        configure_routing(
            username=username,
            password=password,
            host_ips=host_ips,
            hosts=hosts,
            connect_to_hosts=connect_to_hosts,
            disconnect_from_hosts=disconnect_from_hosts,
            protocols=protocols
        )
    # Monitoring actions
    if any(action in ['ping', 'bgp_verification', 'ospf_verification'] for action in args.actions):
        from monitoring_actions import monitor_actions
        monitoring_actions = [action for action in args.actions if action in ['ping', 'bgp_verification', 'ospf_verification']]
        monitor_actions(
            username=username,
            password=password,
            host_ips=host_ips,
            hosts=hosts,
            connect_to_hosts=connect_to_hosts,
            disconnect_from_hosts=disconnect_from_hosts,
            actions=monitoring_actions
        )
    # Backup actions
    if 'backup' in args.actions:
        from backup_actions import backup_config
        backup_config(
            username=username,
            password=password,
            host_ips=host_ips,
            hosts=hosts,
            connect_to_hosts=connect_to_hosts,
            disconnect_from_hosts=disconnect_from_hosts
        )
    if 'baseline' in args.actions:
        from backup_actions import capture_device_baseline
        capture_device_baseline(
            username=username,
            password=password,
            host_ips=host_ips,
            hosts=hosts,
            connect_to_hosts=connect_to_hosts,
            disconnect_from_hosts=disconnect_from_hosts
        )
    # Route monitoring
    if 'route_monitor' in args.actions:
        from route_monitor import route_monitor
        route_monitor(
            username=username,
            password=password,
            host_ips=host_ips,
            hosts=hosts,
            connect_to_hosts=connect_to_hosts,
            disconnect_from_hosts=disconnect_from_hosts,
            interval=interval
        )

if __name__ == "__main__":
    main()
