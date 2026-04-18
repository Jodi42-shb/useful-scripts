#!/usr/bin/env python3
import os
import subprocess
import datetime
import shutil
from pathlib import Path

# Configuration
ADB_PATH = "adb"  # Path to ADB executable (assumes adb is in system PATH)
BACKUP_DIR = f"SDCardBackup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"  # Backup folder with timestamp
SDCARD_PATH = "/sdcard/"  # Source path on device
LOG_FILE = os.path.join(BACKUP_DIR, "pull_sdcard_log.txt")  # Log file for errors and skipped items
SKIP_DIRS = ["Android"]  # Directories to skip (add more if needed, e.g., ["Android", "data", "obb"])

# Function to log messages
def write_log(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} - {message}\n")
    print(message)

# Check if ADB is installed
try:
    subprocess.run([ADB_PATH, "version"], capture_output=True, check=True)
except (subprocess.CalledProcessError, FileNotFoundError):
    print("Error: ADB not found. Please ensure ADB is installed and added to your system PATH.")
    write_log("Error: ADB not found.")
    exit(1)

# Create backup directory
os.makedirs(BACKUP_DIR, exist_ok=True)
print(f"Created backup directory: {BACKUP_DIR}")
write_log(f"Created backup directory: {BACKUP_DIR}")

# Check if device is connected
devices = subprocess.run([ADB_PATH, "devices"], capture_output=True, text=True).stdout
if "device" not in devices.splitlines()[1:]:
    print("Error: No device connected. Ensure USB Debugging is enabled and device is connected.")
    write_log("Error: No device connected.")
    exit(1)

# Get list of files and folders in /sdcard/
print(f"Fetching list of files and folders from {SDCARD_PATH}...")
write_log(f"Fetching list of files and folders from {SDCARD_PATH}...")
result = subprocess.run([ADB_PATH, "shell", f"ls -R {SDCARD_PATH}"], capture_output=True, text=True)
items = result.stdout.splitlines()

# Initialize variables
current_dir = SDCARD_PATH
failed_items = []

# Process each item
for item in items:
    # Check if line indicates a new directory
    if item.endswith(":") and item.startswith("/sdcard/"):
        current_dir = item[:-1]
        continue

    # Skip empty lines or directory headers
    if not item.strip():
        continue

    # Construct full path of the item
    item_path = f"{current_dir}/{item}"

    # Check if item is in a skipped directory
    skip = any(skip_dir in item_path for skip_dir in SKIP_DIRS)
    if skip:
        print(f"Skipping: {item_path} (in skipped directory)")
        write_log(f"Skipped: {item_path} (in skipped directory)")
        continue

    # Create corresponding local directory structure
    relative_path = item_path.replace(SDCARD_PATH, "")
    local_path = os.path.join(BACKUP_DIR, relative_path)
    local_dir = os.path.dirname(local_path)
    os.makedirs(local_dir, exist_ok=True)

    # Attempt to pull the item
    print(f"Pulling: {item_path}")
    write_log(f"Pulling: {item_path}")
    try:
        result = subprocess.run([ADB_PATH, "pull", item_path, local_path], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Successfully pulled: {item_path}")
            write_log(f"Successfully pulled: {item_path}")
        else:
            print(f"Failed to pull: {item_path}. Error: {result.stderr}")
            write_log(f"Failed to pull: {item_path}. Error: {result.stderr}")
            failed_items.append(item_path)
    except subprocess.CalledProcessError as e:
        print(f"Failed to pull: {item_path}. Error: {e.stderr}")
        write_log(f"Failed to pull: {item_path}. Error: {e.stderr}")
        failed_items.append(item_path)

# Summary
print(f"\nBackup completed. Files saved to: {BACKUP_DIR}")
write_log(f"Backup completed. Files saved to: {BACKUP_DIR}")
if failed_items:
    print("Failed to pull the following items (see log for details):")
    for item in failed_items:
        print(f"- {item}")
    write_log(f"Failed items: {', '.join(failed_items)}")
else:
    print("All accessible files were pulled successfully.")
    write_log("All accessible files were pulled successfully.")

# Create a ZIP archive of the backup
zip_file = f"{BACKUP_DIR}.zip"
print(f"Creating ZIP archive: {zip_file}")
write_log(f"Creating ZIP archive: {zip_file}")
shutil.make_archive(BACKUP_DIR, "zip", BACKUP_DIR)
print(f"ZIP archive created: {zip_file}")
write_log(f"ZIP archive created: {zip_file}")