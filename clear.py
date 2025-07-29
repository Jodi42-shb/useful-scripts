# python:_package_and_system_cleanup_windows
import os
import subprocess
import shutil
import sys
import tempfile

# --- CONFIGURATION ---
# A list of essential packages to NOT uninstall.
# These are crucial for Python's package management to function.
ESSENTIAL_PACKAGES = ['pip', 'setuptools', 'wheel', 'distribute']

def uninstall_all_packages():
    """
    Generates a list of all installed packages and uninstalls them one by one,
    skipping the essential packages defined above.
    """
    print("--- Starting Package Uninstall ---")
    print(f"Running in Python interpreter: {sys.executable}")
    print(f"Will NOT uninstall: {', '.join(ESSENTIAL_PACKAGES)}\n")

    try:
        # Get the list of installed packages using 'pip freeze'.
        # Using sys.executable ensures we use the pip associated with this script.
        reqs = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze'])
        installed_packages = [r.decode().split('==')[0] for r in reqs.split()]

        if not installed_packages:
            print("No packages to uninstall.")
            print("--- Package Uninstall Finished ---\n")
            return

        print(f"Found {len(installed_packages)} packages to check.")

        # Create a list of packages to uninstall.
        packages_to_uninstall = [
            p for p in installed_packages if p.lower() not in ESSENTIAL_PACKAGES
        ]

        if not packages_to_uninstall:
            print("No non-essential packages found to uninstall.")
            print("--- Package Uninstall Finished ---\n")
            return
            
        print(f"Attempting to uninstall {len(packages_to_uninstall)} packages...")

        # Uninstall the packages using a single pip command for efficiency.
        # The '-y' flag confirms the uninstallation automatically.
        uninstall_command = [sys.executable, '-m', 'pip', 'uninstall', '-y'] + packages_to_uninstall
        
        # We stream the output to show progress
        process = subprocess.Popen(uninstall_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8')

        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
        
        rc = process.poll()
        if rc == 0:
            print("\nSuccessfully uninstalled packages.")
        else:
            print(f"\nPip uninstall process finished with exit code {rc}. Some packages may not have been uninstalled.")


    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to get list of installed packages. {e}")
    except Exception as e:
        print(f"An unexpected error occurred during uninstallation: {e}")

    print("--- Package Uninstall Finished ---\n")


def clean_python_cache():
    """
    Finds and deletes the pip cache directory located in AppData.
    """
    print("--- Starting Pip Cache Cleanup ---")
    try:
        # The pip cache is typically located in %LOCALAPPDATA%\pip\cache
        local_app_data = os.environ.get('LOCALAPPDATA')
        if not local_app_data:
            print("Error: Could not determine LOCALAPPDATA path.")
            return

        cache_dir = os.path.join(local_app_data, 'pip', 'cache')

        if os.path.exists(cache_dir):
            print(f"Found pip cache at: {cache_dir}")
            print("Deleting cache directory...")
            shutil.rmtree(cache_dir)
            print("Pip cache successfully deleted.")
        else:
            print("Pip cache directory not found. Nothing to do.")

    except PermissionError:
        print(f"Error: Permission denied. Could not delete {cache_dir}.")
        print("Please ensure no other programs are using it and try running the script as an administrator.")
    except Exception as e:
        print(f"An unexpected error occurred during cache cleanup: {e}")

    print("--- Pip Cache Cleanup Finished ---\n")


def clean_temp_folders():
    """
    Cleans out the user's temporary files directory.
    This is a general system cleanup, not specific to Python.
    """
    print("--- Starting System Temp Folder Cleanup ---")
    temp_dir = tempfile.gettempdir()
    print(f"Targeting temp directory: {temp_dir}")
    
    deleted_files_count = 0
    deleted_folders_count = 0
    
    for item in os.listdir(temp_dir):
        item_path = os.path.join(temp_dir, item)
        try:
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.unlink(item_path)
                deleted_files_count += 1
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
                deleted_folders_count += 1
        except PermissionError:
            print(f"  - Skipped (in use): {item_path}")
        except Exception as e:
            print(f"  - Error deleting {item_path}: {e}")
            
    print(f"\nCleanup summary: Deleted {deleted_files_count} files and {deleted_folders_count} folders.")
    print("Note: Some files may have been skipped if they were in use by the system.")
    print("--- System Temp Folder Cleanup Finished ---\n")


def main():
    """
    Main function to run the cleanup operations.
    """
    print("##############################################")
    print("### Python & System Cleanup Script for Windows ###")
    print("##############################################\n")
    print("WARNING: This script will uninstall Python packages and delete files.")
    print("Please read the instructions carefully before proceeding.\n")

    # Ask for user confirmation before proceeding
    while True:
        choice = input("Choose an action:\n"
                       "1. Uninstall ALL non-essential Python packages\n"
                       "2. Clean Pip cache (in AppData)\n"
                       "3. Clean system temporary folder\n"
                       "4. Perform ALL of the above\n"
                       "5. Exit\n"
                       "Enter your choice (1-5): ")
        
        if choice in ['1', '2', '3', '4', '5']:
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 5.")

    if choice == '1':
        uninstall_all_packages()
    elif choice == '2':
        clean_python_cache()
    elif choice == '3':
        clean_temp_folders()
    elif choice == '4':
        uninstall_all_packages()
        clean_python_cache()
        clean_temp_folders()
    elif choice == '5':
        print("Exiting script. No changes were made.")
        return

    print("All selected tasks are complete.")


if __name__ == "__main__":
    main()
