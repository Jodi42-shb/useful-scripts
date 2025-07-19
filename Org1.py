import os
import shutil
import json
from pathlib import Path
import datetime

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
        shutil.move(original_path, dest_path)
        print(f"Restored {rel_path}")
    
    # Delete category folders created during organization
    categories = ['Videos', 'Audio', 'Images', 'Documents', 'Applications', 'Archives', 'Code', 'Ebooks', 'Fonts']
    for category in categories:
        category_path = Path(folder_path) / category
        if category_path.exists():
            shutil.rmtree(category_path)
            print(f"Removed category folder: {category}")
    
    print("Restoration completed!")

def organize_folder(folder_path, backup_dir):
    """Organize files in the folder and its subfolders by file type."""
    # Define file type categories and their extensions
    file_types = {
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

    folder = Path(folder_path)
    
    # Create backup before organizing
    backup_path = create_backup(folder_path, backup_dir)
    
    # Check which categories are needed
    needed_categories = set()
    for root, _, files in os.walk(folder_path):
        for file in files:
            extension = Path(file).suffix.lower()
            for category, extensions in file_types.items():
                if extension in extensions:
                    needed_categories.add(category)
                    break

    # Create only necessary category folders
    for category in needed_categories:
        category_path = folder / category
        category_path.mkdir(exist_ok=True)

    # Move files to their respective category folders
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = Path(root) / file
            # Skip if file is already in a category folder
            if any(category in file_path.parts for category in file_types.keys()):
                continue
            extension = file_path.suffix.lower()
            for category, extensions in file_types.items():
                if extension in extensions:
                    destination = folder / category / file
                    shutil.move(str(file_path), str(destination))
                    print(f"Moved {file} to {category}")
                    break

    # Delete empty directories
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

def main():
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
        organize_folder(folder_path, backup_dir)
    
    print("Operation completed!")

if __name__ == "__main__":
    main()
