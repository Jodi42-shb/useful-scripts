import os
import shutil
from pathlib import Path

def organize_folder(folder_path):
    # Define file type categories and their extensions
    file_types = {
        'Videos': ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.mpeg', '.mpg','.webm','.3gp','.m4v'],
        'Audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'],
        'Images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg', '.webp','.avif','.heic','.heif','.tif'],
        'Documents': ['.doc', '.docx', '.txt', '.pdf', '.rtf', '.odt', '.xlsx', '.xls', '.ppt', '.pptx','.csv'],
        'Applications': ['.exe', '.msi', '.app', '.bat', '.sh', '.jar','.apk','.apkm','.apks'],
        'Archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2','.iso'],
        'Code': ['.py', '.java', '.c', '.cpp', '.cs', '.js', '.html', '.css', '.php', '.rb','.dart','.go','.php','.html','.css','.js','.json','.xml','.yaml','.yml','.toml','.ini','.conf','.log','.md','.txt','.csv','.tsv','.sql','.db','.sqlite','.db3','.db4','.db5','.db6','.db7','.db8','.db9','.db10'],
        'Ebooks': ['.epub', '.mobi', '.azw', '.azw3','.cbz'],
        'Fonts': ['.ttf', '.otf', '.woff', '.woff2']
    }

    # Convert folder_path to Path object
    folder = Path(folder_path)
    
    # Create directories for each category if they don't exist
    for category in file_types.keys():
        category_path = folder / category
        category_path.mkdir(exist_ok=True)

    # Iterate through all files in the folder
    for item in folder.iterdir():
        # Skip if it's a directory
        if item.is_dir():
            continue
            
        # Get file extension in lowercase
        extension = item.suffix.lower()
        
        # Find the appropriate category
        moved = False
        for category, extensions in file_types.items():
            if extension in extensions:
                # Move file to the corresponding category folder
                destination = folder / category / item.name
                shutil.move(str(item), str(destination))
                print(f"Moved {item.name} to {category}")
                moved = True
                break
        
        # If no matching category, move to Others
        if not moved and extension:
            destination = folder / 'Others' / item.name
            shutil.move(str(item), str(destination))
            print(f"Moved {item.name} to Others")

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