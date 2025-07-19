import os
import shutil
import json
from pathlib import Path
import datetime

def get_file_types():
    """Get file type categories and their extensions from Org1.py logic."""
    return {
        'Videos': ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.mpeg', '.mpg','.webm','.3gp','.m4v'],
        'Audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'],
        'Images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg', '.webp','.avif','.heic','.heif','.tif'],
        'Documents': ['.doc', '.docx', '.txt', '.pdf', '.rtf', '.odt', '.xlsx', '.xls', '.ppt', '.pptx','.csv'],
        'Applications': ['.exe', '.msi', '.app', '.bat', '.sh', '.jar','.apk','.apkm','.apks','.ipa'],
        'Archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2','.iso'],
        'Code': ['.py', '.java', '.c', '.cpp', '.cs', '.js', '.html', '.css', '.php', '.rb','.dart','.go','.php','.html','.css','.js','.json','.xml','.yaml','.yml','.toml','.ini','.conf','.log','.md','.txt','.csv','.tsv','.sql','.db','.sqlite','.db3','.db4','.db5','.db6','.db7','.db8','.db9','.db10'],
        'Ebooks': ['.epub', '.mobi', '.azw', '.azw3','.cbz'],
        'Fonts': ['.ttf', '.otf', '.woff', '.woff2']
    }

def create_backup(folder_path, backup_dir):
    """Create a backup of the folder structure and file locations."""
    backup_path = Path(backup_dir) / f"backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    file_structure = {}
    
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = Path(root) / file
            rel_path = str(file_path.relative_to(folder_path))
            file_structure[rel_path] = str(file_path)
    
    with open(backup_path, 'w') as f:
        json.dump(file_structure, f, indent=4)
    
    print(f"Backup created at {backup_path}")
    return backup_path

def restore_backup(folder_path, backup_file):
    """Restore the original folder structure from a backup file."""
    with open(backup_file, 'r') as f:
        file_structure = json.load(f)
    
    for rel_path, original_path in file_structure.items():
        dest_path = Path(folder_path) / rel_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        if os.path.exists(original_path):
            shutil.move(original_path, dest_path)
            print(f"Restored {rel_path}")
        else:
            print(f"Warning: Original file not found - {original_path}")
    
    # Delete category folders created during organization
    file_types = get_file_types()
    for category in file_types.keys():
        category_path = Path(folder_path) / category
        if category_path.exists() and category_path.is_dir():
            try:
                shutil.rmtree(category_path)
                print(f"Removed category folder: {category}")
            except OSError as e:
                print(f"Could not remove {category}: {e}")
    
    print("Restoration completed!")

def get_files_to_organize(folder_path, recursive):
    """Get list of files to organize based on recursive option."""
    files_to_process = []
    
    if recursive:
        # Process all files in folder and subfolders
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = Path(root) / file
                files_to_process.append(file_path)
    else:
        # Process only files in the root folder
        folder = Path(folder_path)
        for file_path in folder.iterdir():
            if file_path.is_file():
                files_to_process.append(file_path)
    
    return files_to_process

def organize_folder(folder_path, recursive, backup_dir, create_backup_flag):
    """Organize files in the folder by file type."""
    file_types = get_file_types()
    folder = Path(folder_path)
    
    # Create backup if requested
    if create_backup_flag:
        backup_path = create_backup(folder_path, backup_dir)
        print(f"Backup created: {backup_path}")
    else:
        print("Skipping backup creation as requested.")
    
    # Get files to process
    files_to_process = get_files_to_organize(folder_path, recursive)
    
    # Determine which categories are needed by scanning files first
    needed_categories = set()
    for file_path in files_to_process:
        # Skip if file is already in a category folder
        if any(category in file_path.parts for category in file_types.keys()):
            continue
            
        extension = file_path.suffix.lower()
        for category, extensions in file_types.items():
            if extension in extensions:
                needed_categories.add(category)
                break
    
    # Create only necessary category folders
    for category in needed_categories:
        category_path = folder / category
        category_path.mkdir(exist_ok=True)
        print(f"Created category folder: {category}")
    
    # Move files to their respective category folders
    files_moved = 0
    for file_path in files_to_process:
        # Skip if file is already in a category folder
        if any(category in file_path.parts for category in file_types.keys()):
            continue
            
        extension = file_path.suffix.lower()
        for category, extensions in file_types.items():
            if extension in extensions:
                destination = folder / category / file_path.name
                try:
                    shutil.move(str(file_path), str(destination))
                    print(f"Moved {file_path.name} to {category}")
                    files_moved += 1
                except Exception as e:
                    print(f"Error moving {file_path.name}: {e}")
                break
    
    # Delete empty directories (only if processing recursively)
    if recursive:
        for root, dirs, _ in os.walk(folder_path, topdown=False):
            for dir_name in dirs:
                dir_path = Path(root) / dir_name
                # Skip category folders
                if dir_name not in file_types.keys():
                    try:
                        dir_path.rmdir()
                        print(f"Deleted empty directory: {dir_path}")
                    except OSError:
                        pass  # Directory not empty or other error
    
    print(f"\nOrganization completed! {files_moved} files moved.")

def main():
    print("File Organizer Script")
    print("=" * 30)
    
    folder_path = input("Enter the folder path to organize (leave blank for current directory): ").strip()
    if not folder_path:
        folder_path = os.getcwd()
    
    if not os.path.exists(folder_path):
        print(f"Error: The folder '{folder_path}' does not exist.")
        return
    
    backup_dir = input("Enter the backup directory path (leave blank for current directory): ").strip()
    if not backup_dir:
        backup_dir = os.getcwd()
    
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # Ask for recursive processing
    recursive_input = input("Process files recursively (including subfolders)? (y/N): ").strip().lower()
    recursive = recursive_input == 'y'
    
    # Ask for backup creation
    create_backup_input = input("Create a backup before organizing? (y/N): ").strip().lower()
    create_backup_flag = create_backup_input == 'y'
    
    action = input("Choose action - 'organize' or 'restore' (leave blank for organize): ").strip().lower()
    
    if action == 'restore':
        backup_file = input("Enter the path to the backup JSON file: ").strip()
        if not os.path.exists(backup_file):
            print(f"Error: The backup file '{backup_file}' does not exist.")
            return
        print(f"Restoring files in {folder_path}...")
        restore_backup(folder_path, backup_file)
    else:
        print(f"Organizing files in {folder_path}...")
        print(f"Recursive processing: {'Yes' if recursive else 'No'}")
        print(f"Backup creation: {'Yes' if create_backup_flag else 'No'}")
        organize_folder(folder_path, recursive, backup_dir, create_backup_flag)
    
    print("Operation completed!")

if __name__ == "__main__":
    main()
