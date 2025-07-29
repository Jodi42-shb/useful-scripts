import os
import shutil
from pathlib import Path

def find_first_image(folder_path):
    """Find the first image file (1.ext) in the folder to use as cover."""
    extensions = ['.jpg', '.jpeg', '.png', '.webp']
    for ext in extensions:
        cover_path = os.path.join(folder_path, f"1{ext}")
        if os.path.isfile(cover_path):
            return cover_path
    # Fallback: return first image found
    for file in sorted(os.listdir(folder_path)):
        if file.lower().endswith(tuple(extensions)):
            return os.path.join(folder_path, file)
    return None

def organize_manga_inplace(source_dir):
    """Reorganize manga folders in-place into Mihon-compatible structure."""
    # Supported image extensions
    image_extensions = ('.jpg', '.jpeg', '.png', '.webp')

    # Iterate through each folder in source directory
    for series_folder in os.listdir(source_dir):
        series_path = Path(source_dir) / series_folder
        if not series_path.is_dir():
            continue

        # Use folder name as series title
        series_title = series_folder

        # Create Chapter 1 folder inside series folder
        chapter_path = series_path / "Chapter 1"
        chapter_path.mkdir(exist_ok=True)

        # Move images to Chapter 1
        for file in sorted(os.listdir(series_path)):
            file_path = series_path / file
            if file_path.is_file() and file.lower().endswith(image_extensions):
                dst_file = chapter_path / file
                # Avoid overwriting by adding a suffix if needed
                if dst_file.exists():
                    base, ext = os.path.splitext(file)
                    counter = 1
                    while dst_file.exists():
                        dst_file = chapter_path / f"{base}_{counter}{ext}"
                        counter += 1
                shutil.move(file_path, dst_file)

        # Create .nomedia file in series folder
        nomedia_file = series_path / ".nomedia"
        nomedia_file.touch()

        # Find and set cover image (1.ext)
        cover_image = find_first_image(chapter_path)
        if cover_image:
            cover_ext = os.path.splitext(cover_image)[1]
            cover_dst = series_path / f"cover{cover_ext}"
            if not cover_dst.exists():
                shutil.copy2(cover_image, cover_dst)

        print(f"Reorganized series: {series_title}")

def main():
    # User-defined source directory (OneDrive folder)
    source_dir = input("Enter the OneDrive directory containing manga folders (e.g., C:\\Users\\YourName\\OneDrive\\manga_folders): ").strip()
    
    if not os.path.isdir(source_dir):
        print(f"Error: Source directory '{source_dir}' does not exist.")
        return
    
    try:
        organize_manga_inplace(source_dir)
        print(f"Successfully reorganized manga in {source_dir}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()