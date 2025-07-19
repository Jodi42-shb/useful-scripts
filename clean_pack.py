import os
import shutil
from pathlib import Path
import humanize  # pip install humanize

# List the folders you want to target
TARGET_FOLDERS = [
    Path.home() / ".cache" / "huggingface",
    Path(os.environ.get("LOCALAPPDATA", "")) / "pip" / "Cache",
    Path(os.environ.get("LOCALAPPDATA", "")) / "Temp",
    Path(os.environ.get("APPDATA", "")) / "Python",
    Path(os.environ.get("LOCALAPPDATA", "")) / "Programs"  # Review before use
]

def get_size(path):
    total = 0
    for root, dirs, files in os.walk(path, topdown=True):
        for f in files:
            fp = os.path.join(root, f)
            if os.path.exists(fp):
                total += os.path.getsize(fp)
    return total

def main():
    print("\n=== Cache & Temp Folder Cleaner ===\n")
    for folder in TARGET_FOLDERS:
        if folder.exists():
            folder_size = get_size(folder)
            print(f"{folder} : {humanize.naturalsize(folder_size)}")
            user = input(f"Do you want to remove this folder? (y/N): ").strip().lower()
            if user == "y":
                try:
                    shutil.rmtree(folder)
                    print(f"Removed {folder}\n")
                except Exception as e:
                    print(f"Error removing {folder}: {e}")
            else:
                print("Skipped\n")
        else:
            print(f"{folder} does not exist or already removed.\n")

    print("Cleanup complete. Review remaining large folders if needed.")

if __name__ == "__main__":
    main()

