import os
import shutil
from pathlib import Path

def denest_folder(root_path):
    """
    Moves all files from subfolders to the root folder, maintaining unique filenames.
    
    Args:
        root_path (str): Path to the root folder to denest
    """
    # Convert to Path object for easier handling
    root = Path(root_path).resolve()
    
    # Walk through all subdirectories
    for folder, _, files in os.walk(root):
        folder_path = Path(folder)
        
        # Skip the root folder itself
        if folder_path == root:
            continue
            
        # Process each file in the current subdirectory
        for file in files:
            source_path = folder_path / file
            
            # Create destination path
            dest_path = root / file
            
            # Handle filename conflicts by adding a number suffix
            counter = 1
            while dest_path.exists():
                base, ext = os.path.splitext(file)
                new_filename = f"{base}_{counter}{ext}"
                dest_path = root / new_filename
                counter += 1
            
            try:
                # Move the file to the root folder
                shutil.move(str(source_path), str(dest_path))
                print(f"Moved: {source_path} -> {dest_path}")
            except Exception as e:
                print(f"Error moving {source_path}: {e}")
    
    # Clean up empty directories
    for folder, _, _ in os.walk(root, topdown=False):
        folder_path = Path(folder)
        if folder_path == root:
            continue
        try:
            folder_path.rmdir()
            print(f"Removed empty directory: {folder_path}")
        except OSError:
            # Directory not empty or other error, skip
            pass

def main():
    # Get the folder path from user input or use current directory
    folder_path = input("Enter the folder path to denest (press Enter for current directory): ").strip()
    if not folder_path:
        folder_path = os.getcwd()
    
    # Verify the folder exists
    if not os.path.isdir(folder_path):
        print(f"Error: {folder_path} is not a valid directory")
        return
    
    print(f"Denesting folder: {folder_path}")
    denest_folder(folder_path)
    print("Denesting complete!")

if __name__ == "__main__":
    main()