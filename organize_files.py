import os
import shutil
from datetime import datetime
import zipfile

def get_file_extension(file_name):
    """Return the file extension in lowercase without the dot."""
    ext = os.path.splitext(file_name)[1].lower().lstrip('.')
    return ext if ext else 'no_extension'

def create_backup(source_dir):
    """Create a zip backup of the source directory."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_{timestamp}.zip"
    backup_path = os.path.join(source_dir, backup_name)
    
    with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(source_dir):
            for file in files:
                if file != backup_name:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source_dir)
                    zipf.write(file_path, arcname)
    print(f"Backup created: {backup_path}")
    return backup_path

def organize_files(source_dir, create_backup_option=True):
    """
    Organize files in source_dir into subfolders based on file extensions.
    If create_backup_option is True, create a backup before organizing.
    """
    # File type categories with extensions (dots removed for consistency)
    file_types = {
        'Videos': ['mp4', 'mkv', 'avi', 'mov', 'wmv', 'flv', 'mpeg', 'mpg', 'webm', '3gp', 'm4v'],
        'Audio': ['mp3', 'wav', 'flac', 'aac', 'ogg', 'wma', 'm4a'],
        'Images': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'svg', 'webp', 'avif', 'heic', 'heif', 'tif'],
        'Documents': ['doc', 'docx', 'txt', 'pdf', 'rtf', 'odt', 'xlsx', 'xls', 'ppt', 'pptx', 'csv'],
        'Applications': ['exe', 'msi', 'app', 'bat', 'sh', 'jar', 'apk', 'apkm', 'apks'],
        'Archives': ['zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'iso'],
        'Code': ['py', 'java', 'c', 'cpp', 'cs', 'js', 'html', 'css', 'php', 'rb', 'dart', 'go', 'json', 'xml', 'yaml', 'yml', 'toml', 'ini', 'conf', 'log', 'md', 'tsv', 'sql', 'db', 'sqlite', 'db3', 'db4', 'db5', 'db6', 'db7', 'db8', 'db9', 'db10','ps1'],
        'Ebooks': ['epub', 'mobi', 'azw', 'azw3', 'cbz'],
        'Fonts': ['ttf', 'otf', 'woff', 'woff2']
    }

    # Create a reverse mapping of extension to category
    ext_to_category = {}
    for category, extensions in file_types.items():
        for ext in extensions:
            ext_to_category[ext.lower()] = category

    # Create backup if requested
    if create_backup_option:
        create_backup(source_dir)

    # Get all files in the directory
    files = [f for f in os.listdir(source_dir) if os.path.isfile(os.path.join(source_dir, f))]

    # Track which categories are actually used
    used_categories = set()

    # Organize files
    for file in files:
        # Skip backup files
        if file.startswith('backup_') and file.endswith('.zip'):
            continue

        ext = get_file_extension(file)
        print(f"Processing file: {file}, Extension: {ext}")  # Debug output

        # Determine category
        category = ext_to_category.get(ext, 'Others')
        used_categories.add(category)

        # Log categorization
        print(f"File: {file} -> Category: {category}")

        # Create category folder if it doesn't exist
        category_path = os.path.join(source_dir, category)
        if not os.path.exists(category_path):
            os.makedirs(category_path)

        # Move file to category folder
        source_path = os.path.join(source_dir, file)
        dest_path = os.path.join(category_path, file)
        
        # Handle duplicate filenames
        base, extension = os.path.splitext(file)
        counter = 1
        while os.path.exists(dest_path):
            new_filename = f"{base}_{counter}{extension}"
            dest_path = os.path.join(category_path, new_filename)
            counter += 1

        try:
            shutil.move(source_path, dest_path)
            print(f"Moved {file} to {category}")
        except Exception as e:
            print(f"Error moving {file}: {str(e)}")

    # Print summary
    print("\nOrganization complete!")
    print(f"Files organized into: {', '.join(sorted(used_categories))}")

if __name__ == "__main__":
    # Get the directory to organize
    source_directory = input("Enter the directory path to organize (or press Enter for current directory): ").strip()
    if not source_directory:
        source_directory = os.getcwd()

    # Verify directory exists
    if not os.path.isdir(source_directory):
        print("Error: Invalid directory path")
        exit(1)

    # Ask about backup
    backup_choice = input("Create a backup before organizing? (y/n): ").lower().strip()
    create_backup_flag = backup_choice == 'y'

    organize_files(source_directory, create_backup_flag)