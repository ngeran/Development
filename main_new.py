import yaml
import os
import sys

def get_host_data(host_type):
    """
    Collect host details from user input.
    """
    hosts = []  # Initialize an empty list to store host dictionaries
    while True:
        print(f"\nEntering Details for {host_type}:")
        host_name = input(f"\nEnter the {host_type} Host Name (or 'done' to finish): ")
        if host_name.lower() == 'done':
            break

        host_ip = input(f"Enter the {host_type} IP: ")
        function = input(f"Enter the {host_type} Function: ")

        host = {
            'host_name': host_name,
            'host_ip': host_ip,
            'function': function
        }
        hosts.append(host)
    return hosts

def save_yaml_file(servicenow_change_number, yaml_data, base_dir="changes"):
    """
    Create directories and save the YAML file in changes/CHO1234567/.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.join(script_dir, base_dir)

    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
        print(f"Created Directory: {base_dir}")

    change_dir = os.path.join(base_dir, servicenow_change_number)

    if not os.path.exists(change_dir):
        os.makedirs(change_dir)
        print(f"Created Directory: {change_dir}")

    filename = f"{servicenow_change_number}_CI.yml"
    full_path = os.path.join(change_dir, filename)

    with open(full_path, 'w') as file:
        file.write(yaml_data)
    print(f"File saved to {full_path}")

def load_yaml_file(servicenow_change_number, base_dir="changes"):
    """
    Load and return the content of an existing YAML file if it exists.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.join(script_dir, base_dir)

    file_path = os.path.join(base_dir, servicenow_change_number, f"{servicenow_change_number}_CI.yml")
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return yaml.safe_load(file), file_path
    return None, None

def main():
    try:
        # Get ServiceNow Change Number First:
        servicenow_change_number = input("Enter the ServiceNow Change Number (e.g., CH01234567): ").strip().upper()

        # Check if the YAML file already exists
        existing_data, file_path = load_yaml_file(servicenow_change_number)

        # Fallback if file not found in default location
        if existing_data is None:
            print(f"\nNo existing file found for {servicenow_change_number} in the default 'changes/' directory.")
            custom_dir = input("Enter the absolute path to the 'changes/' directory (or press Enter to proceed): ").strip()
            if custom_dir:
                existing_data, file_path = load_yaml_file(servicenow_change_number, custom_dir)

        use_existing = False
        if existing_data is not None:
            print(f"\nExisting file found at: {file_path}")
            print("Current Content:")
            print("-----------------------------")
            print(yaml.dump(existing_data, default_flow_style=False))

            while True:
                choice = input("Do you want to use the existing file (y) or create a new one (n)? ").lower()
                if choice in ['y', 'n']:
                    break
                print("Please enter 'y' or 'n'.")

            if choice == 'y':
                use_existing = True

        # If using existing file
        if use_existing:
            while True:
                confirmation = input("Confirm using this file? (y/n): ").lower()
                if confirmation in ['y', 'n']:
                    break
                print("Please enter 'y' or 'n'.")

            if confirmation == 'y':
                print("Existing file will be kept as is.")
                return  # Exit the program, no further action needed
            else:
                print("Discarding existing file selection, proceeding to create a new one.")

        # Initialize the data structure
        data = {
            'servicenow_change_number': servicenow_change_number,
            'hosts': {
                'routers': [],
                'switches': []
            }
        }

        # Collect router data
        print("\n=== Router Configuration ===")
        data['hosts']['routers'] = get_host_data("Router")

        # Collect switch data
        print("\n=== Switch Configuration ===")
        data['hosts']['switches'] = get_host_data("Switch")

        # Convert the YAML string for verification
        yaml_output = yaml.dump(data, default_flow_style=False)
        print("\nGenerated YAML configuration: ")
        print("-----------------------------")
        print(yaml_output)

        # Verify Host Data with the User
        while True:
            configuration = input("Is this configuration correct? (y/n): ").lower()
            if configuration in ['y', 'n']:
                break
            print("Please Enter 'y' or 'n'.")

        # Save the file if approved by the user
        if configuration == 'y':
            save_yaml_file(servicenow_change_number, yaml_output)
        else:
            print("Configuration not Approved.")

    except KeyboardInterrupt:
        print("\nScript terminated by user (Ctrl+C). Exiting gracefully.")
        sys.exit(0)  # Exit with status code 0 (success)

if __name__ == "__main__":
    main()
