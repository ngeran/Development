import os  # For file and directory operations
import yaml  # For parsing the interface_actions.yml file

# Directory of this script (scripts/)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def load_interface_actions(file_path="../data/interface_actions.yml"):
    """Load interface actions from the YAML file.

    Args:
        file_path (str): Path to interface_actions.yml, relative to scripts/.

    Returns:
        dict: Parsed YAML data containing actions, or None if loading fails.
    """
    full_path = os.path.join(SCRIPT_DIR, file_path)
    try:
        with open(full_path, 'r') as yaml_file:
            return yaml.safe_load(yaml_file)
    except FileNotFoundError:
        print(f"Error: YAML file '{full_path}' not found.")
        return None
    except yaml.YAMLError as error:
        print(f"Error parsing the YAML: {error}")
        return None

def display_action_menu(actions):
    """Display the menu of interface actions and return the selected action.

    Args:
        actions (dict): Dictionary of actions from YAML.

    Returns:
        str or None: Selected action key (e.g., 'configure'), or None if quit.
    """
    # Debug: Print the actions structure to verify
    print(f"Debug: actions = {actions}")

    print("+" + "-" * 38 + "+")  # Top border
    print("| {:^37} |".format("Interface Actions Menu"))  # Title
    print("+" + "-" * 38 + "+")  # Separator

    if actions and 'actions' in actions:
        for i, action in enumerate(actions['actions']):
            print("| {:2}. {:33} |".format(i + 1, action['name']))
        print("+" + "-" * 38 + "+")  # Bottom border

        choice = input("Select an action (1-{} or 'q' to quit): ".format(len(actions['actions'])))
        if choice.lower() == 'q':
            print("Exiting action menu.")
            return None
        try:
            action_index = int(choice) - 1
            if 0 <= action_index < len(actions['actions']):
                return actions['actions'][action_index]['action']
            else:
                print(f"Error: Select a number between 1 and {len(actions['actions'])}.")
                return None
        except ValueError:
            print("Error: Invalid input. Please enter a number or 'q'.")
            return None
    else:
        print("| {:^38} |".format("No actions available."))
        print("+" + "-" * 38 + "+")
        return None

if __name__ == "__main__":
    # Test the menu standalone
    actions = load_interface_actions()
    selected = display_action_menu(actions)
    print(f"Selected action: {selected}")
