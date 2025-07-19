import os
import shutil
from pathlib import Path

def organize_folder(folder_path):
    # Define file type categories and their extensions
    file_types = {
        'Videos': ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.mpeg', '.mpg'],
        'Audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'],
        'Images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg', '.webp'],
        'Documents': ['.doc', '.docx', '.txt', '.pdf', '.rtf', '.odt', '.xlsx', '.xls', '.ppt', '.pptx'],
        'Applications': ['.exe', '.msi', '.app', '.bat', '.sh', '.jar'],
        'Archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
        'Code': ['.py', '.java', '.c', '.cpp', '.cs', '.js', '.html', '.css', '.php', '.rb'],
        'Ebooks': ['.epub', '.mobi', '.azw', '.azw3'],
        'Fonts': ['.ttf', '.otf', '.woff', '.woff2']
    }

    # Convert folder_path to Path object
    folder = Path(folder_path)
    
    # Check which categories are needed based on existing files
    needed_categories = set()
    for item in folder.iterdir():
        if item.is_file():
            extension = item.suffix.lower()
            for category, extensions in file_types.items():
                if extension in extensions:
                    needed_categories.add(category)
                    break

    # Create only necessary category folders
    for category in needed_categories:
        category_path = folder / category
        category_path.mkdir(exist_ok=True)

    # Move files to their respective category folders
    for item in folder.iterdir():
        # Skip if it's a directory
        if item.is_dir():
            continue
            
        # Get file extension in lowercase
        extension = item.suffix.lower()
        
        # Find and move to the appropriate category
        for category, extensions in file_types.items():
            if extension in extensions:
                destination = folder / category / item.name
                shutil.move(str(item), str(destination))
                print(f"Moved {item.name} to {category}")
                break
        # Files with unrecognized extensions are left untouched

def main():
    # Get the folder path from user (default to current directory)
    folder_path = input("Enter the folder path to organize (leave blank for current directory): ").strip()
    if not folder_path:
        folder_path = os.getcwd()
    
    # Verify if the folder exists
    if not os.path.exists(folder_path):
        print(f"Error: The folder '{folder_path}' does not exist.")
        return
    
    print(f"Organizing files in {folder_path}...")
    organize_folder(folder_path)
    print("File organization completed!")

if __name__ == "__main__":
    main()