#!/usr/bin/env python3
import os
import shutil
from datetime import datetime
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_backup_folder(base_path):
    """Create a backup folder with timestamp in the specified directory."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(base_path, f"nomedia_backup_{timestamp}")
    os.makedirs(backup_path, exist_ok=True)
    return backup_path

def remove_nomedia_files(root_path, max_retries=3, retry_delay=1):
    """Remove .nomedia files and move them to a backup folder."""
    backup_path = create_backup_folder(root_path)
    nomedia_files_moved = []
    
    for root, dirs, files in os.walk(root_path):
        if "nomedia_backup" in root:
            continue
            
        for file in files:
            if file.lower() == ".nomedia":
                file_path = os.path.join(root, file)
                for attempt in range(max_retries):
                    try:
                        # Create relative path structure in backup folder
                        rel_path = os.path.relpath(root, root_path)
                        backup_subfolder = os.path.join(backup_path, rel_path)
                        os.makedirs(backup_subfolder, exist_ok=True)
                        
                        # Move the file to backup
                        backup_file_path = os.path.join(backup_subfolder, file)
                        shutil.move(file_path, backup_file_path)
                        nomedia_files_moved.append((file_path, backup_file_path))
                        logger.info(f"Moved: {file_path} to {backup_file_path}")
                        break
                    except PermissionError as e:
                        if "[WinError 380]" in str(e):
                            logger.warning(f"OneDrive sync error for {file_path}. Retrying {attempt+1}/{max_retries}")
                            time.sleep(retry_delay)
                            continue
                        else:
                            logger.error(f"Permission error for {file_path}: {e}")
                            break
                    except Exception as e:
                        logger.error(f"Error moving {file_path}: {e}")
                        break
    
    return nomedia_files_moved, backup_path

def restore_nomedia_files(backup_path):
    """Restore .nomedia files from the backup folder."""
    if not os.path.exists(backup_path):
        logger.error(f"Backup folder {backup_path} does not exist")
        return
    
    for root, dirs, files in os.walk(backup_path):
        for file in files:
            if file.lower() == ".nomedia":
                backup_file_path = os.path.join(root, file)
                # Calculate original path
                rel_path = os.path.relpath(root, backup_path)
                original_path = os.path.join(os.path.dirname(backup_path), rel_path, file)
                
                try:
                    # Ensure original directory exists
                    os.makedirs(os.path.dirname(original_path), exist_ok=True)
                    shutil.move(backup_file_path, original_path)
                    logger.info(f"Restored: {backup_file_path} to {original_path}")
                except Exception as e:
                    logger.error(f"Error restoring {backup_file_path}: {e}")

def main():
    root_path = input("Enter the path to scan for .nomedia files (e.g., C:\\Users\\YourName\\OneDrive): ")
    if not os.path.exists(root_path):
        logger.error("Invalid path provided")
        return
    
    print("Choose an option:")
    print("1. Remove .nomedia files (with backup)")
    print("2. Restore .nomedia files from backup")
    choice = input("Enter 1 or 2: ")
    
    if choice == "1":
        nomedia_files_moved, backup_path = remove_nomedia_files(root_path)
        print(f"\nOperation complete. {len(nomedia_files_moved)} .nomedia files moved to {backup_path}")
        if nomedia_files_moved:
            print("To restore these files later, run this script again and choose option 2.")
            print(f"Backup folder: {backup_path}")
    elif choice == "2":
        backup_path = input("Enter the backup folder path: ")
        restore_nomedia_files(backup_path)
        print("Restore operation complete.")
    else:
        print("Invalid choice. Please run the script again and select 1 or 2.")

if __name__ == "__main__":
    main()