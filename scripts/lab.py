import os
import sys
import yaml
# Load the YAML file
def load_yaml(file_path: str):

    # Step 1: Verify file existence
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' does not exists.")
        return None

    if not os.path.isfile(file_path):
        print(f"Error: '{file_path}' is not a file.")
        return None

    # Step 2: Load and parse the YAML file
    try:
        # Open file in read mode
        with open(file_path, 'r') as file:
        # Parse YAML into Python object
            yaml_data = yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' could not be opened.")
        return None
    except yaml.YAMLError as error:
        print(f"Error: Invalid YAML format in '{file_path}' : {error}")
        return None
    except Exception as e:
        print(f"Error: Unexpected issue loading '{file_path}': {e}")
        return None

    # Step 3: Basic validation - check if data was loaded
    if yaml_data is None:
        print(f"Error: '{file_path}' is empty or contains no valid YAML data.")
        return None

    if not isinstance(yaml_data, dict):
        print(f"Error: '{file_path}' must parse to a dictionary, got {type(yaml_data)} instead.")
        return None

    # Success: Return the parsed data
    print(f"Successfully loaded and validated '{file_path}'.")
    return yaml_data

def main():
    file_path = "../data/host.yml"
    load_yaml(file_path)

if __name__ == '__main__':
    main()
