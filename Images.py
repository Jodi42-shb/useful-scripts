import os
import shutil
from datetime import datetime
import tkinter as tk
from tkinter import filedialog
import exifread
import mimetypes

def get_file_date(file_path):
    """Extract the date from a file's EXIF data (for images) or file modification time."""
    if file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff')):
        try:
            with open(file_path, 'rb') as f:
                tags = exifread.process_file(f, details=False)
                date_str = tags.get('EXIF DateTimeOriginal') or tags.get('DateTime')
                if date_str:
                    return datetime.strptime(str(date_str), '%Y:%m:%d %H:%M:%S')
        except Exception:
            pass
    return datetime.fromtimestamp(os.path.getmtime(file_path))

def select_directory():
    """Open a dialog for selecting a directory."""
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askdirectory(title="Select Directory with Images and Videos")
    return path

def get_user_choice(prompt, options):
    """Get user input from a list of options."""
    print(prompt)
    for i, option in enumerate(options, 1):
        print(f"{i}. {option}")
    while True:
        try:
            choice = int(input("Enter the number of your choice: "))
            if 1 <= choice <= len(options):
                return options[choice - 1]
            print(f"Please enter a number between 1 and {len(options)}.")
        except ValueError:
            print("Please enter a valid number.")

def is_folder_accessible(folder_path):
    """Check if a folder is accessible (to handle OneDrive sync issues)."""
    try:
        os.listdir(folder_path)
        return True
    except (PermissionError, OSError):
        return False

def find_existing_folder(base_path, target_name):
    """Find an existing folder with a matching name (case-insensitive)."""
    for folder in os.listdir(base_path):
        if folder.lower() == target_name.lower():
            return os.path.join(base_path, folder)
    return None

def organize_images_videos():
    """Main function to organize images and videos."""
    # Select source directory
    source_dir = select_directory()
    if not source_dir:
        print("No directory selected. Exiting.")
        return

    # Ask for recursive or non-recursive
    recursive = get_user_choice("Process subdirectories recursively?", ["Yes", "No"]) == "Yes"

    # Ask for organization method
    org_method = get_user_choice(
        "Organize by:", ["Year and Month", "Year only", "Month only"]
    )

    # Ask for conflict handling
    conflict_action = get_user_choice(
        "Handle conflicting filenames by:", ["Rename", "Leave in place"]
    )

    # Supported media extensions
    media_extensions = {
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.avif', '.webp', '.heic', # Images
        '.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv'    # Videos
    }

    # Month names for folder formatting
    month_names = {
        1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
        7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December"
    }

    # Walk through directory
    processed_files = 0
    for root, _, files in os.walk(source_dir) if recursive else [(source_dir, [], os.listdir(source_dir))]:
        for file in files:
            if os.path.splitext(file)[1].lower() in media_extensions:
                file_path = os.path.join(root, file)
                date = get_file_date(file_path)
                
                # Determine destination folder
                if org_method == "Year and Month":
                    month_folder = f"{date.month:02d}-{month_names[date.month]}"
                    year_folder = str(date.year)
                    # Check for existing year folder
                    existing_year = find_existing_folder(source_dir, year_folder)
                    year_path = existing_year or os.path.join(source_dir, year_folder)
                    # Check for existing month folder
                    existing_month = find_existing_folder(year_path, month_folder) if existing_year else None
                    dest_folder = existing_month or os.path.join(year_path, month_folder)
                elif org_method == "Year only":
                    year_folder = str(date.year)
                    existing_year = find_existing_folder(source_dir, year_folder)
                    dest_folder = existing_year or os.path.join(source_dir, year_folder)
                else:  # Month only
                    month_folder = f"{date.month:02d}-{month_names[date.month]}"
                    existing_month = find_existing_folder(source_dir, month_folder)
                    dest_folder = existing_month or os.path.join(source_dir, month_folder)

                # Create destination folder if it doesn't exist
                os.makedirs(dest_folder, exist_ok=True)

                # Handle file movement
                dest_path = os.path.join(dest_folder, file)
                if os.path.exists(dest_path) and file_path != dest_path:
                    if conflict_action == "Rename":
                        base, ext = os.path.splitext(file)
                        counter = 1
                        while os.path.exists(dest_path):
                            new_name = f"{base}_{counter}{ext}"
                            dest_path = os.path.join(dest_folder, new_name)
                            counter += 1
                    else:
                        print(f"Skipping {file}: already exists in {dest_folder}")
                        continue

                try:
                    shutil.move(file_path, dest_path)
                    processed_files += 1
                    print(f"Moved {file} to {dest_path}")
                except Exception as e:
                    print(f"Error moving {file}: {e}")

    print(f"\nProcessed {processed_files} files.")

    # Ask about removing empty folders
    if get_user_choice("Remove empty folders?", ["Yes", "No"]) == "Yes":
        removed_folders = 0
        for root, dirs, _ in os.walk(source_dir, topdown=False):
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                if not is_folder_accessible(dir_path):
                    print(f"Skipping folder {dir_path}: Access denied or sync issue")
                    continue
                if not os.listdir(dir_path):
                    try:
                        os.rmdir(dir_path)
                        removed_folders += 1
                        print(f"Removed empty folder: {dir_path}")
                    except Exception as e:
                        print(f"Error removing folder {dir_path}: {e}")
        print(f"Removed {removed_folders} empty folders.")

if __name__ == "__main__":
    organize_images_videos()