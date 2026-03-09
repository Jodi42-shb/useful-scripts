import os
import shutil
import json
from pathlib import Path
import datetime


def get_file_types():
    """Define comprehensive file type categories and their extensions."""
    return {
        "Videos": [
            ".mp4",
            ".mkv",
            ".avi",
            ".mov",
            ".wmv",
            ".flv",
            ".mpeg",
            ".mpg",
            ".webm",
            ".3gp",
            ".m4v",
            ".ts",
            ".mts",
            ".m2ts",
            ".vob",
            ".rm",
            ".rmvb",
            ".ogv",
            ".divx",
            ".xvid",
            ".f4v",
            ".mxf",
            ".asf",
            ".amv",
            ".drc",
            ".mng",
            ".yuv",
            ".roq",
            ".nsv",
            ".bik",
            ".wtv",
            ".trp",
            ".mp2",
            ".mpv",
            ".mpe",
            ".mpg4",
            ".m1v",
            ".m2v",
            ".m2p",
            ".m2t",
            ".m4p",
            ".m4b",
            ".m4r",
            ".m4u",
            ".m4e",
            ".mod",
            ".tod",
            ".dat",
            ".dv",
            ".h264",
            ".h265",
            ".hevc",
            ".avchd",
            ".vp6",
            ".vp7",
            ".vp8",
            ".vp9",
            ".ogm",
            ".ogx",
            ".qt",
            ".fli",
            ".flc",
            ".mve",
            ".ivf",
            ".skm",
            ".evo",
        ],
        "Audio": [
            ".mp3",
            ".wav",
            ".flac",
            ".aac",
            ".ogg",
            ".wma",
            ".m4a",
            ".alac",
            ".aiff",
            ".ape",
            ".amr",
            ".opus",
            ".ra",
            ".mid",
            ".midi",
            ".mpa",
            ".mpc",
            ".wv",
            ".tta",
            ".ac3",
            ".dts",
            ".au",
            ".snd",
            ".oga",
            ".spx",
            ".caf",
            ".voc",
            ".mka",
            ".m3u",
            ".pls",
        ],
        "Images": [
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".bmp",
            ".tiff",
            ".tif",
            ".svg",
            ".webp",
            ".avif",
            ".heic",
            ".heif",
            ".raw",
            ".cr2",
            ".nef",
            ".orf",
            ".sr2",
            ".arw",
            ".dng",
            ".ico",
            ".jfif",
            ".jpe",
            ".jp2",
            ".j2k",
            ".jpf",
            ".jpx",
            ".jpm",
            ".mj2",
            ".psd",
            ".ai",
            ".eps",
            ".indd",
            ".cdr",
        ],
        "Documents": [
            ".doc",
            ".docx",
            ".txt",
            ".pdf",
            ".rtf",
            ".odt",
            ".xlsx",
            ".xls",
            ".xlsm",
            ".xlsb",
            ".xltx",
            ".ppt",
            ".pptx",
            ".pps",
            ".ppsx",
            ".csv",
            ".tsv",
            ".tex",
            ".wpd",
            ".md",
            ".log",
            ".pages",
            ".numbers",
            ".key",
            ".odp",
            ".ods",
            ".odg",
            ".odf",
            ".epub",
            ".djvu",
            ".fb2",
            ".xps",
        ],
        "Applications": [
            ".exe",
            ".msi",
            ".app",
            ".bat",
            ".sh",
            ".jar",
            ".apk",
            ".apkm",
            ".apks",
            ".deb",
            ".rpm",
            ".bin",
            ".cmd",
            ".com",
            ".gadget",
            ".wsf",
            ".msu",
            ".dmg",
            ".pkg",
            ".run",
        ],
        "Archives": [
            ".zip",
            ".rar",
            ".7z",
            ".tar",
            ".gz",
            ".bz2",
            ".xz",
            ".iso",
            ".cab",
            ".arj",
            ".lzh",
            ".ace",
            ".uue",
            ".bz",
            ".z",
            ".001",
            ".jar",
            ".tgz",
            ".tbz2",
            ".lzma",
            ".lz",
            ".zst",
            ".cpio",
        ],
        "Code": [
            ".py",
            ".java",
            ".c",
            ".cpp",
            ".cs",
            ".js",
            ".ts",
            ".html",
            ".htm",
            ".css",
            ".php",
            ".rb",
            ".dart",
            ".go",
            ".json",
            ".xml",
            ".yaml",
            ".yml",
            ".toml",
            ".ini",
            ".conf",
            ".log",
            ".md",
            ".sh",
            ".bat",
            ".pl",
            ".swift",
            ".kt",
            ".kts",
            ".scala",
            ".rs",
            ".asm",
            ".sql",
            ".db",
            ".sqlite",
            ".db3",
            ".db4",
            ".db5",
            ".db6",
            ".db7",
            ".db8",
            ".db9",
            ".db10",
            ".r",
            ".m",
            ".mat",
            ".ipynb",
            ".jsp",
            ".asp",
            ".aspx",
            ".vue",
            ".jsx",
            ".tsx",
            ".h",
            ".hpp",
            ".hxx",
            ".sln",
            ".vb",
            ".vbs",
            ".ps1",
            ".psm1",
            ".psd1",
            ".clj",
            ".cljs",
            ".groovy",
            ".erl",
            ".ex",
            ".exs",
            ".lua",
            ".f90",
            ".f95",
            ".for",
            ".f",
            ".fs",
            ".fsi",
            ".fsx",
            ".fsscript",
        ],
        "Ebooks": [
            ".epub",
            ".mobi",
            ".azw",
            ".azw3",
            ".cbz",
            ".cbr",
            ".pdf",
            ".fb2",
            ".djvu",
            ".lit",
            ".prc",
            ".ibooks",
            ".pdb",
        ],
        "Fonts": [
            ".ttf",
            ".otf",
            ".woff",
            ".woff2",
            ".eot",
            ".fon",
            ".pfa",
            ".pfb",
            ".afm",
            ".bdf",
            ".sfd",
        ],
    }


def create_backup(folder_path, backup_dir):
    """Create a JSON backup of the folder structure and file locations."""
    backup_path = (
        Path(backup_dir)
        / f"backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    file_structure = {}

    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = Path(root) / file
            rel_path = str(file_path.relative_to(folder_path))
            file_structure[rel_path] = str(file_path)

    with open(backup_path, "w") as f:
        json.dump(file_structure, f, indent=4)

    print(f"Backup created at {backup_path}")
    return backup_path


def restore_backup(folder_path, backup_file):
    """Restore the original folder structure from a backup file."""
    backup_path = Path(backup_file)
    if not backup_path.exists():
        print(f"Error: Backup file '{backup_file}' does not exist.")
        return

    try:
        with open(backup_path, "r") as f:
            file_structure = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Backup file '{backup_file}' is corrupted or invalid.")
        return

    folder = Path(folder_path)
    restored_files = 0
    skipped_files = 0

    for rel_path, original_path in file_structure.items():
        dest_path = folder / rel_path
        src_path = Path(original_path)

        if not src_path.exists():
            print(
                f"Warning: Cannot restore '{rel_path}' - source file '{original_path}' not found."
            )
            skipped_files += 1
            continue

        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src_path), str(dest_path))
            print(f"Restored {rel_path}")
            restored_files += 1
        except (OSError, shutil.Error) as e:
            print(f"Error restoring '{rel_path}': {e}")
            skipped_files += 1

    # Delete category folders created during organization
    file_types = get_file_types()
    for category in file_types.keys():
        category_path = folder / category
        if category_path.exists():
            try:
                shutil.rmtree(category_path)
                print(f"Removed category folder: {category}")
            except OSError as e:
                print(f"Error removing category folder '{category}': {e}")

    print(
        f"Restoration completed! Restored: {restored_files} files, Skipped: {skipped_files} files."
    )


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


def handle_duplicates(destination, file_name):
    """Handle duplicate filenames by appending a counter."""
    dest_path = destination / file_name
    base, ext = dest_path.stem, dest_path.suffix
    counter = 1
    while dest_path.exists():
        new_name = f"{base}_{counter}{ext}"
        dest_path = destination / new_name
        counter += 1
    return dest_path


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
        # Add 'Others' if no match
        if extension and not any(
            extension == f".{ext}" for cat in file_types.values() for ext in cat
        ):
            needed_categories.add("Others")

    # Create only necessary category folders
    for category in sorted(needed_categories):
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
        category = "Others"
        for cat, extensions in file_types.items():
            if extension in extensions:
                category = cat
                break

        destination = folder / category
        dest_path = handle_duplicates(destination, file_path.name)
        try:
            shutil.move(str(file_path), str(dest_path))
            print(f"Moved {file_path.name} to {category}")
            files_moved += 1
        except (OSError, shutil.Error) as e:
            print(f"Error moving {file_path.name}: {e}")

    # Delete empty directories (only if processing recursively)
    if recursive:
        for root, dirs, _ in os.walk(folder_path, topdown=False):
            for dir_name in dirs:
                dir_path = Path(root) / dir_name
                # Skip category folders
                if dir_name not in file_types.keys() and dir_name != "Others":
                    try:
                        dir_path.rmdir()
                        print(f"Deleted empty directory: {dir_path}")
                    except OSError:
                        pass  # Directory not empty or other error

    print(f"\nOrganization completed! {files_moved} files moved.")


def main():
    print("Advanced File Organizer Script")
    print("=" * 40)

    folder_path = input(
        "Enter the folder path to organize (leave blank for current directory): "
    ).strip()
    if not folder_path:
        folder_path = os.getcwd()

    if not os.path.exists(folder_path):
        print(f"Error: The folder '{folder_path}' does not exist.")
        return

    backup_dir = input(
        "Enter the backup directory path (leave blank for current directory): "
    ).strip()
    if not backup_dir:
        backup_dir = os.getcwd()

    if not os.path.exists(backup_dir):
        try:
            os.makedirs(backup_dir)
        except OSError as e:
            print(f"Error creating backup directory '{backup_dir}': {e}")
            return

    # Ask for recursive processing
    recursive_input = (
        input("Process files recursively (including subfolders)? (y/N): ")
        .strip()
        .lower()
    )
    recursive = recursive_input == "y"

    # Ask for backup creation
    create_backup_input = (
        input("Create a backup before organizing? (y/N): ").strip().lower()
    )
    create_backup_flag = create_backup_input == "y"

    action = (
        input("Choose action - 'organize' or 'restore' (leave blank for organize): ")
        .strip()
        .lower()
    )

    if action == "restore":
        backup_file = input("Enter the path to the backup JSON file: ").strip()
        if not backup_file:
            print("Error: Backup file path is required for restore.")
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
