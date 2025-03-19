# Main.py
import yaml  # For parsing the automation_jobs.yml file
import subprocess  # For running selected scripts as subprocesses

def load_automation_tasks(automation_jobs="data/automation_jobs.yml"):
    """
    Load the available automation tasks from the YAML file
    located in /data/automation_jobs.yml
    Args:
        automation_jobs (str): Path to YAML file containing job definitions
    Returns:
        dict: A dictionary containing the jobs, or None if loading fails
    """
    try:
        with open(automation_jobs, 'r') as yaml_file:
            jobs = yaml.safe_load(yaml_file)
        return jobs
    except FileNotFoundError:
        print(f"Error: YAML file '{automation_jobs}' not found.")  # Fixed variable name
        return None
    except yaml.YAMLError as error:
        print(f"Error parsing the YAML: {error}")
        return None

def display_automation_jobs(jobs):
    """
    Display the list of automation jobs and return the user’s selected script.
    Args:
        jobs (dict): Dictionary of automation jobs from YAML
    Returns:
        str or None: Path to the selected script, or None if no selection or quit
    """
    # Display the table header
    print("+" + "-" * 38 + "+")  # Top border
    print("| {:^37} |".format("Available Automation Jobs"))  # Title
    print("+" + "-" * 38 + "+")  # Separator

    # Check if there are jobs to display
    if jobs and 'jobs' in jobs:
        # List each job with a number
        for i, job in enumerate(jobs['jobs']):
            print("| {:2}. {:33} |".format(i + 1, job['name']))  # Job items
        print("+" + "-" * 38 + "+")  # Bottom border

        # Prompt user for selection
        choice = input("Select a job number to run (1-{} or 'q' to quit): ".format(len(jobs['jobs'])))

        # Handle quit option
        if choice.lower() == 'q':
            print("Exiting.")
            return None

        # Validate and return the selected script
        try:
            job_index = int(choice) - 1  # Convert to 0-based index
            if 0 <= job_index < len(jobs['jobs']):
                return jobs['jobs'][job_index]['script']  # Return script path
            else:
                print(f"Error: Please select a number between 1 and {len(jobs['jobs'])}.")
                return None
        except ValueError:
            print("Error: Invalid input. Please enter a number or 'q'.")
            return None
    else:
        # Handle case with no jobs
        print("| {:^38} |".format("No Jobs to display."))
        print("+" + "-" * 38 + "+")  # Bottom border
        return None

def main():
    """Main function to load automation tasks, get user selection, and run the selected script."""
    # Load the automation jobs from YAML
    automation_jobs = load_automation_tasks()

    # Display jobs and get the selected script
    selected_script = display_automation_jobs(automation_jobs)

    # If a script was selected, run it
    if selected_script:
        print(f"Running script: {selected_script}")
        try:
            # Execute the selected script as a subprocess
            subprocess.run(["python", selected_script], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running {selected_script}: {e}")
        except FileNotFoundError:
            print(f"Error: Script '{selected_script}' not found.")

if __name__ == "__main__":
    main()
