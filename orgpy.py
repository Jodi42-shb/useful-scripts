import os
import shutil
from pathlib import Path

def organize_folder(folder_path):
    # Define file type categories and their extensions
    file_types = {
        'Videos': [
            '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.mpeg', '.mpg', '.webm', '.3gp', '.m4v',
            '.ts', '.mts', '.m2ts', '.vob', '.rm', '.rmvb', '.ogv', '.divx', '.xvid', '.f4v', '.mxf',
            '.asf', '.amv', '.drc', '.mng', '.yuv', '.roq', '.nsv', '.bik', '.wtv', '.trp', '.mp2',
            '.mpv', '.mpe', '.mpg4', '.m1v', '.m2v', '.m2p', '.m2t', '.m4p', '.m4b', '.m4r', '.m4u',
            '.m4e', '.mod', '.tod', '.dat', '.dv', '.h264', '.h265', '.hevc', '.avchd', '.vp6', '.vp7',
            '.vp8', '.vp9', '.ogm', '.ogx', '.qt', '.fli', '.flc', '.mve', '.ivf', '.skm', '.evo'
        ],
        'Audio': [
            '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.alac', '.aiff', '.ape', '.amr',
            '.opus', '.ra', '.mid', '.midi', '.mpa', '.mpc', '.wv', '.tta', '.ac3', '.dts', '.au', '.snd',
            '.oga', '.spx', '.caf', '.voc', '.mka', '.m3u', '.pls'
        ],
        'Images': [
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.svg', '.webp', '.avif', '.heic',
            '.heif', '.raw', '.cr2', '.nef', '.orf', '.sr2', '.arw', '.dng', '.ico', '.jfif', '.jpe',
            '.jp2', '.j2k', '.jpf', '.jpx', '.jpm', '.mj2', '.psd', '.ai', '.eps', '.indd', '.cdr'
        ],
        'Documents': [
            '.doc', '.docx', '.txt', '.pdf', '.rtf', '.odt', '.xlsx', '.xls', '.xlsm', '.xlsb', '.xltx',
            '.ppt', '.pptx', '.pps', '.ppsx', '.csv', '.tsv', '.tex', '.wpd', '.md', '.log', '.pages',
            '.numbers', '.key', '.odp', '.ods', '.odg', '.odf', '.epub', '.djvu', '.fb2', '.xps'
        ],
        'Applications': [
            '.exe', '.msi', '.app', '.bat', '.sh', '.jar', '.apk', '.apkm', '.apks', '.deb', '.rpm',
            '.bin', '.cmd', '.com', '.gadget', '.wsf', '.msu', '.dmg', '.pkg', '.run'
        ],
        'Archives': [
            '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.iso', '.cab', '.arj', '.lzh', '.ace',
            '.uue', '.bz', '.z', '.001', '.jar', '.tgz', '.tbz2', '.lzma', '.lz', '.zst', '.cpio'
        ],
        'Code': [
            '.py', '.java', '.c', '.cpp', '.cs', '.js', '.ts', '.html', '.htm', '.css', '.php', '.rb',
            '.dart', '.go', '.json', '.xml', '.yaml', '.yml', '.toml', '.ini', '.conf', '.log', '.md',
            '.sh', '.bat', '.pl', '.swift', '.kt', '.kts', '.scala', '.rs', '.asm', '.sql', '.db',
            '.sqlite', '.db3', '.db4', '.db5', '.db6', '.db7', '.db8', '.db9', '.db10', '.r', '.m',
            '.mat', '.ipynb', '.jsp', '.asp', '.aspx', '.vue', '.jsx', '.tsx', '.h', '.hpp', '.hxx',
            '.sln', '.vb', '.vbs', '.ps1', '.psm1', '.psd1', '.clj', '.cljs', '.groovy', '.erl', '.ex',
            '.exs', '.lua', '.f90', '.f95', '.for', '.f', '.fs', '.fsi', '.fsx', '.fsscript'
        ],
        'Ebooks': [
            '.epub', '.mobi', '.azw', '.azw3', '.cbz', '.cbr', '.pdf', '.fb2', '.djvu', '.lit', '.prc',
            '.ibooks', '.pdb'
        ],
        'Fonts': [
            '.ttf', '.otf', '.woff', '.woff2', '.eot', '.fon', '.pfa', '.pfb', '.afm', '.bdf', '.sfd'
        ]
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