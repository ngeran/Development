import os
import yaml
import jinja2

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

def render_template(template_data):
    """
    Render a Jinja2 template for a single host.
    Args:
        host (dict): Host data to render
        template_dir (str): Directory containing templates
        template_name (str): Name of the template file (default: 'interface_template.j2')
    Returns:
        str: Rendered configuration, or None if rendering fails
    """
    # Set up the Jinja2 environment to load the template from the 'templates' directory
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(searchpath='../templates')
    )

    try:
        # Load the Jinja2 template from the 'templates' directory
        template = env.get_template('interface_template.j2')
    except jinja2.exceptions.TempateNotFound as error:
        print(f"Error laoding template: {error}")
        return

    # Render the template with the data from the YAML file
    config = template.render(hosts=template_data)

    # Print the rendered configuration
    print("\nRendered Configuration:")
    print(config)

    return config
