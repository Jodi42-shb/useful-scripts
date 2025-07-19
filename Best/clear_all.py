# WinCleaner.py
# A Comprehensive and Transparent Windows System Cleanup Utility (v3 - Corrected)

import os
import shutil
import ctypes
import subprocess
import logging
import math
from datetime import datetime, timedelta

# Attempt to import winshell for Recycle Bin functionality.
# If it's not installed, the corresponding feature will be disabled.
try:
    import winshell
    WINSHELL_AVAILABLE = True
except ImportError:
    WINSHELL_AVAILABLE = False

# --- CONFIGURATION BLOCK ---
# Users can enable or disable cleanup tasks by setting these flags to True or False.
CONFIG = {
    "CLEAN_USER_TEMP": True,
    "CLEAN_WINDOWS_TEMP": True,
    "CLEAN_WINDOWS_UPDATE_CACHE": True,
    "CLEAN_PREFETCH": False,  # Disabled by default due to performance impact.
    "EMPTY_RECYCLE_BIN": True,
    "VERBOSE": True, # Set to False for silent operation.
    "LOG_TO_FILE": True,
    "LOG_FILE_PATH": "WinCleaner_Log.txt",
    "TEMP_FILE_AGE_DAYS": 2 # Delete temp files older than this many days.
}

# --- UTILITY FUNCTIONS ---

def is_admin():
    """
    Checks if the script is running with administrative privileges.
    This is crucial for accessing system folders and managing services.
    Returns True if running as admin, False otherwise.
    """
    try:
        # This call checks the process token for membership in the Administrators group.
        return ctypes.windll.shell32.IsUserAnAdmin()!= 0
    except AttributeError:
        # This will occur on non-Windows systems.
        return False

def human_readable_size(size_bytes):
    """Converts a size in bytes to a human-readable format (KB, MB, GB)."""
    if size_bytes <= 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

def get_folder_size(path):
    """Recursively calculates the total size of a folder."""
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                # Skip if it's a symlink or file doesn't exist
                if not os.path.islink(fp) and os.path.exists(fp):
                    total_size += os.path.getsize(fp)
    except FileNotFoundError:
        return 0
    return total_size

# --- CORE CLEANUP FUNCTIONS ---

def clear_directory_recursively(path, age_days=0):
    """
    Custom function to recursively delete files and folders.
    This is superior to shutil.rmtree(ignore_errors=True) because it provides
    granular error logging for each file/folder that fails to be deleted.

    Args:
        path (str): The root directory to clean.
        age_days (int): If > 0, only deletes files older than this many days.

    Returns:
        A tuple (bytes_deleted, items_skipped_count).
    """
    if not os.path.isdir(path):
        logging.warning(f"Directory not found, skipping: {path}")
        return 0, 0

    total_bytes_deleted = 0
    items_skipped = 0
    cutoff_time = datetime.now() - timedelta(days=age_days)

    # Walk the directory tree from the top down to delete files.
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            try:
                if age_days > 0:
                    file_mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if file_mod_time >= cutoff_time:
                        continue # Skip file if it's not old enough

                file_size = os.path.getsize(file_path)
                os.remove(file_path)
                total_bytes_deleted += file_size
                logging.info(f"Deleted file: {file_path}")

            except (PermissionError, OSError) as e:
                items_skipped += 1
                logging.error(f"Could not delete file: {file_path}. Reason: {e}")

    # Walk the directory tree from the bottom up to delete empty folders.
    for dirpath, dirnames, filenames in os.walk(path, topdown=False):
        if not os.listdir(dirpath): # Check if directory is empty
            try:
                os.rmdir(dirpath)
                logging.info(f"Deleted empty directory: {dirpath}")
            except (PermissionError, OSError) as e:
                items_skipped += 1
                logging.error(f"Could not delete directory: {dirpath}. Reason: {e}")

    return total_bytes_deleted, items_skipped

def clear_temp_folders():
    """
    Cleans the user and system temporary folders based on the configured file age.
    """
    logging.info("--- Starting Temporary Folders Cleanup ---")
    total_bytes_cleared = 0
    total_items_skipped = 0
    age_days = CONFIG["TEMP_FILE_AGE_DAYS"]

    # 1. User Temp Folder
    if CONFIG["CLEAN_USER_TEMP"]:
        user_temp_path = os.path.expandvars(r'%TEMP%')
        if CONFIG["VERBOSE"]:
            print(f"Cleaning user temp folder: {user_temp_path} (deleting files older than {age_days} days)...")
        bytes_cleared, items_skipped = clear_directory_recursively(user_temp_path, age_days)
        total_bytes_cleared += bytes_cleared
        total_items_skipped += items_skipped
        if CONFIG["VERBOSE"]:
            print(f"  > Cleared {human_readable_size(bytes_cleared)}.")

    # 2. Windows Temp Folder
    if CONFIG["CLEAN_WINDOWS_TEMP"]:
        windows_temp_path = os.path.join(os.getenv('SystemRoot', 'C:\\Windows'), 'Temp')
        if CONFIG["VERBOSE"]:
            print(f"Cleaning Windows temp folder: {windows_temp_path} (deleting files older than {age_days} days)...")
        bytes_cleared, items_skipped = clear_directory_recursively(windows_temp_path, age_days)
        total_bytes_cleared += bytes_cleared
        total_items_skipped += items_skipped
        if CONFIG["VERBOSE"]:
            print(f"  > Cleared {human_readable_size(bytes_cleared)}.")

    logging.info("--- Finished Temporary Folders Cleanup ---")
    return total_bytes_cleared, total_items_skipped

def clear_software_distribution():
    """
    Clears the Windows Update download cache. This requires stopping and
    restarting critical system services in a transactional manner.
    """
    logging.info("--- Starting Windows Update Cache Cleanup ---")
    if CONFIG["VERBOSE"]:
        print("Cleaning Windows Update cache...")

    cache_path = os.path.join(os.getenv('SystemRoot', 'C:\\Windows'), 'SoftwareDistribution', 'Download')
    services = ['wuauserv', 'bits']
    bytes_cleared = 0
    items_skipped = 0

    try:
        # Step 1: Stop services
        for service in services:
            if CONFIG["VERBOSE"]: print(f"  > Stopping service: {service}...")
            subprocess.run(['net', 'stop', service], check=True, capture_output=True)
            logging.info(f"Service '{service}' stopped successfully.")

        # Step 2: Delete contents of the cache folder
        bytes_cleared, items_skipped = clear_directory_recursively(cache_path, age_days=0)

    except subprocess.CalledProcessError as e:
        error_message = e.stderr.decode(errors='ignore').strip() if e.stderr else "No error output."
        logging.error(f"Failed to stop a service. Command: '{e.cmd}'. Error: {error_message}")
        items_skipped = len(os.listdir(cache_path)) if os.path.isdir(cache_path) else 1
    except Exception as e:
        logging.error(f"An unexpected error occurred during SoftwareDistribution cleanup: {e}")
        items_skipped = len(os.listdir(cache_path)) if os.path.isdir(cache_path) else 1
    finally:
        # Step 3: Restart services in a 'finally' block to ensure they are
        # always restarted, even if the deletion fails. This is critical for system stability.
        for service in services:
            if CONFIG["VERBOSE"]: print(f"  > Starting service: {service}...")
            try:
                subprocess.run(['net', 'start', service], check=True, capture_output=True)
                logging.info(f"Service '{service}' started successfully.")
            except subprocess.CalledProcessError as e:
                error_message = e.stderr.decode(errors='ignore').strip() if e.stderr else "No error output."
                logging.critical(f"CRITICAL: Failed to restart service '{service}'. Please restart it manually. Error: {error_message}")
                if CONFIG["VERBOSE"]:
                    print(f"  [!!] CRITICAL: Failed to restart service '{service}'. Please restart it manually.")

    if CONFIG["VERBOSE"]:
        print(f"  > Cleared {human_readable_size(bytes_cleared)}.")
    logging.info("--- Finished Windows Update Cache Cleanup ---")
    return bytes_cleared, items_skipped

def clear_prefetch():
    """
    Clears the Prefetch folder. This is an advanced/aggressive option that can
    temporarily degrade performance as Windows rebuilds the optimization files.
    """
    logging.info("--- Starting Prefetch Cleanup ---")
    if CONFIG["VERBOSE"]:
        print("Cleaning Prefetch folder (aggressive option)...")
        print("  [!] Warning: This may temporarily slow down application launch times.")

    prefetch_path = os.path.join(os.getenv('SystemRoot', 'C:\\Windows'), 'Prefetch')
    bytes_cleared, items_skipped = clear_directory_recursively(prefetch_path, age_days=0)

    if CONFIG["VERBOSE"]:
        print(f"  > Cleared {human_readable_size(bytes_cleared)}.")
    logging.info("--- Finished Prefetch Cleanup ---")
    return bytes_cleared, items_skipped

def empty_recycle_bin():
    """
    Empties the Recycle Bin for all users using the 'winshell' library.
    """
    if not WINSHELL_AVAILABLE:
        logging.warning("Winshell library not found. Skipping Recycle Bin cleanup.")
        if CONFIG["VERBOSE"]:
            print("Skipping Recycle Bin: 'winshell' module not installed. (Run: pip install winshell)")
        return 0, 0

    logging.info("--- Starting Recycle Bin Cleanup ---")
    if CONFIG["VERBOSE"]:
        print("Emptying Recycle Bin...")

    try:
        # Get current size before emptying
        recycle_bin = winshell.recycle_bin()
        initial_size = sum(item.size() for item in recycle_bin)

        # Empty the bin silently.
        recycle_bin.empty(confirm=False, show_progress=False, sound=False)
        bytes_cleared = initial_size
        items_skipped = 0
        logging.info("Recycle Bin emptied successfully.")
        if CONFIG["VERBOSE"]:
            print(f"  > Cleared {human_readable_size(bytes_cleared)}.")

    except Exception as e:
        bytes_cleared = 0
        items_skipped = 1 # Mark as one general failure.
        logging.error(f"Failed to empty Recycle Bin. Reason: {e}")
        if CONFIG["VERBOSE"]:
            print("  > Failed to empty Recycle Bin.")

    logging.info("--- Finished Recycle Bin Cleanup ---")
    return bytes_cleared, items_skipped

# --- MAIN EXECUTION BLOCK ---

def main():
    """
    Main function to orchestrate the cleanup process.
    """
    # CORRECTED: Configure logging using the specific path from CONFIG
    if CONFIG["LOG_TO_FILE"]:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename=CONFIG["LOG_FILE_PATH"],
            filemode='a' # Append to the log file
        )
    else:
        # If not logging to file, log to console
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    logging.info("=============================================")
    logging.info("WinCleaner Script Started")
    print("WinCleaner.py - A Comprehensive Windows Cleanup Utility")
    print("="*50)

    # 1. Check for Administrator Privileges
    if not is_admin():
        message = "Administrative privileges are required to run this script. Please re-run as Administrator."
        logging.critical(message)
        print(f"\nERROR: {message}")
        return

    total_bytes_freed = 0
    total_items_skipped_overall = 0

    # CORRECTED: Execute tasks based on their specific config flag
    if CONFIG["CLEAN_USER_TEMP"] or CONFIG["CLEAN_WINDOWS_TEMP"]:
        bytes_freed, items_skipped = clear_temp_folders()
        total_bytes_freed += bytes_freed
        total_items_skipped_overall += items_skipped

    if CONFIG["CLEAN_WINDOWS_UPDATE_CACHE"]:
        bytes_freed, items_skipped = clear_software_distribution()
        total_bytes_freed += bytes_freed
        total_items_skipped_overall += items_skipped

    if CONFIG["CLEAN_PREFETCH"]:
        bytes_freed, items_skipped = clear_prefetch()
        total_bytes_freed += bytes_freed
        total_items_skipped_overall += items_skipped

    if CONFIG["EMPTY_RECYCLE_BIN"]:
        bytes_freed, items_skipped = empty_recycle_bin()
        total_bytes_freed += bytes_freed
        total_items_skipped_overall += items_skipped

    # Final Summary
    print("-" * 50)
    print("Cleanup Summary:")
    print(f"  Total space freed: {human_readable_size(total_bytes_freed)}")
    if total_items_skipped_overall > 0:
        print(f"  Items skipped due to errors: {total_items_skipped_overall}")
        # CORRECTED: Refer to the log file path from CONFIG
        if CONFIG["LOG_TO_FILE"]:
            print(f"  (Check '{CONFIG['LOG_FILE_PATH']}' for details)")
    print("="*50)

    logging.info(f"Cleanup finished. Total space freed: {human_readable_size(total_bytes_freed)}. Items skipped: {total_items_skipped_overall}.")
    logging.info("=============================================\n")

if __name__ == "__main__":
    main()