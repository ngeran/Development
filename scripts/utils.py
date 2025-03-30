import os
import yaml
import jinja2

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(SCRIPT_DIR, '../templates')

def load_yaml(file_path):
    """
    Load a YAML file and return its contents.
    Args:
        file_path (str): Path to the YAML file
    Returns:
        dict: Parsed YAML data, or None if loading fails
    """
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found. ")
        return None
    try:
        with open(file_path, 'r') as file:
            return yaml.safe_load(file)
    except yaml.YAMLError as error:
        print(f"Error: Invalid YAML syntax in '{file_path}': {error}")
        return None
    except Exception as error:
        print(f"Unexpected Error loading '{file_path}': {error} ")
        return None

def group_devices(devices, attribute):
    """
    Group devices by a specified attribute (e.g., 'host_location', 'product_family').
    Args:
        devices (list): List of device dictionaries
        attribute (str): Key to group by
    Returns:
        dict: Devices grouped by the attribute value
    """
    grouped = {}
    for device in devices:
        # Default to Unknown if attribute is missing
        value = device.get(attribute, 'Unknown')
        if value not in grouped:
            grouped[value] = []
        grouped[value].append(device)
    return grouped

def render_template(host, template_name):
    """
    Render a Jinja2 template for a single host.
    Args:
        host (dict): Host data to render
        template_dir (str): Directory containing templates
        template_name (str): Name of the template file (default: 'interface_template.j2')
    Returns:
        str: Rendered configuration, or None if rendering fails
    """
    if not os.path.exists(TEMPLATE_DIR):
        print(f"Error: Template directory '{TEMPLATE_DIR} does not exist.")
        return None
    # Set up the Jinja2 environment to load the template from the 'templates' directory
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(TEMPLATE_DIR)
    )
    try:
        # Load the Jinja2 template from the 'templates' directory
        template = env.get_template(template_name)
    except jinja2.exceptions.TempateNotFound as error:
        print(f"Error laoding template '{template_name}' in '{TEMPLATE_DIR}': {error}")
        return

    # Render the template with the data from the YAML file
    # Pass as list for template compatibility
    config = template.render(hosts=[host])

    # Print the rendered configuration
    print(f"\nRendered Configuration for {host['host_name']} using '{template_name}':\n{config}")
    print(config)

    return config
