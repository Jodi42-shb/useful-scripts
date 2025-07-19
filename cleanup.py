import os
import shutil
import psutil
import winshell
from pathlib import Path
import time

def get_size(start_path='.'):
    """Calculate total size of files in a directory recursively."""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            try:
                total_size += os.path.getsize(fp)
            except (OSError, PermissionError):
                continue
    return total_size

def clean_temp_files():
    """Delete files in Windows TEMP and Prefetch folders."""
    temp_path = os.path.expandvars(r'%LocalAppData%\Temp')
    prefetch_path = r'C:\Windows\Prefetch'
    deleted_size = 0
    deleted_count = 0

    # Clean TEMP folder
    print("Cleaning TEMP folder...")
    try:
        for item in os.listdir(temp_path):
            item_path = os.path.join(temp_path, item)
            try:
                if os.path.isfile(item_path):
                    os.remove(item_path)
                    deleted_size += os.path.getsize(item_path)
                    deleted_count += 1
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path, ignore_errors=True)
                    deleted_size += get_size(item_path)
                    deleted_count += 1
            except (PermissionError, OSError) as e:
                print(f"Could not delete {item_path}: {e}")
    except Exception as e:
        print(f"Error accessing TEMP folder: {e}")

    # Clean Prefetch folder
    print("Cleaning Prefetch folder...")
    try:
        for item in os.listdir(prefetch_path):
            item_path = os.path.join(prefetch_path, item)
            try:
                if os.path.isfile(item_path):
                    os.remove(item_path)
                    deleted_size += os.path.getsize(item_path)
                    deleted_count += 1
            except (PermissionError, OSError) as e:
                print(f"Could not delete {item_path}: {e}")
    except Exception as e:
        print(f"Error accessing Prefetch folder: {e}")

    print(f"Deleted {deleted_count} items, freed {deleted_size / (1024 * 1024):.2f} MB")

def clear_recycle_bin():
    """Clear the Windows Recycle Bin."""
    print("Clearing Recycle Bin...")
    try:
        winshell.recycle_bin().empty(confirm=False, show_progress=False, sound=False)
        print("Recycle Bin cleared successfully.")
    except Exception as e:
        print(f"Error clearing Recycle Bin: {e}")

def disk_usage_summary():
    """Display disk usage for all drives."""
    print("\nDisk Usage Summary:")
    for disk in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(disk.mountpoint)
            print(f"Drive {disk.mountpoint}:")
            print(f"  Total: {usage.total / (1024**3):.2f} GB")
            print(f"  Used: {usage.used / (1024**3):.2f} GB")
            print(f"  Free: {usage.free / (1024**3):.2f} GB")
            print(f"  Usage: {usage.percent}%")
        except Exception as e:
            print(f"Error accessing {disk.mountpoint}: {e}")

def main():
    print("Windows Cleanup Tool")
    print("===================")
    
    # Run cleanup tasks
    clean_temp_files()
    clear_recycle_bin()
    disk_usage_summary()
    
    print("\nCleanup completed! Press Enter to exit.")
    input()

if __name__ == "__main__":
    # Ensure script runs with admin privileges for Prefetch and Recycle Bin access
    try:
        import ctypes
        if not ctypes.windll.shell32.IsUserAnAdmin():
            print("This script requires administrative privileges. Please run as Administrator.")
            input("Press Enter to exit.")
            exit()
        main()
    except Exception as e:
        print(f"An error occurred: {e}")
        input("Press Enter to exit.")