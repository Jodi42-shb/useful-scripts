#!/usr/bin/env python3
import os
import shutil
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    filename='reorganize_log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def find_first_image(chapter_path):
    """Find the first image file (1.ext) in the Chapter 1 folder to use as cover."""
    extensions = ['.jpg', '.jpeg', '.png', '.webp']
    try:
        for ext in extensions:
            cover_path = os.path.join(chapter_path, f"1{ext}")
            if os.path.isfile(cover_path):
                return cover_path
        # Fallback: return first image found in Chapter 1
        for file in sorted(os.listdir(chapter_path)):
            if file.lower().endswith(tuple(extensions)):
                return os.path.join(chapter_path, file)
        logging.warning(f"No valid image found for cover in {chapter_path}")
        return None
    except Exception as e:
        logging.error(f"Error finding cover image in {chapter_path}: {e}")
        return None

def organize_manga_inplace(source_dir, create_nomedia):
    """Reorganize manga folders in-place into Mihon-compatible structure."""
    # Supported image extensions
    image_extensions = ('.jpg', '.jpeg', '.png', '.webp')

    # Iterate through each folder in source directory
    for series_folder in os.listdir(source_dir):
        series_path = Path(source_dir) / series_folder
        if not series_path.is_dir():
            logging.info(f"Skipping non-directory: {series_folder}")
            continue

        # Use folder name as series title
        series_title = series_folder
        logging.info(f"Processing series: {series_title}")

        try:
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
                    try:
                        shutil.move(file_path, dst_file)
                        logging.info(f"Moved {file_path} to {dst_file}")
                    except Exception as e:
                        logging.error(f"Error moving {file_path} to {dst_file}: {e}")
                        continue

            # Find and copy cover image from Chapter 1
            cover_image = find_first_image(chapter_path)
            if cover_image:
                cover_ext = os.path.splitext(cover_image)[1]
                cover_dst = series_path / f"cover{cover_ext}"
                if not cover_dst.exists():
                    try:
                        shutil.copy2(cover_image, cover_dst)
                        logging.info(f"Copied cover {cover_image} to {cover_dst}")
                    except Exception as e:
                        logging.error(f"Error copying cover {cover_image} to {cover_dst}: {e}")
                else:
                    logging.warning(f"Cover {cover_dst} already exists")
            else:
                logging.warning(f"No cover image found for {series_title}")

            # Create .nomedia file if requested
            if create_nomedia:
                nomedia_file = series_path / ".nomedia"
                try:
                    nomedia_file.touch()
                    logging.info(f"Created .nomedia in {series_path}")
                except Exception as e:
                    logging.error(f"Error creating .nomedia in {series_path}: {e}")

            print(f"Reorganized series: {series_title}")
        except Exception as e:
            logging.error(f"Error processing series {series_title}: {e}")
            print(f"Error processing {series_title}. Check reorganize_log.txt for details.")

def main():
    # User-defined source directory (OneDrive folder)
    source_dir = input("Enter the OneDrive directory containing manga folders (e.g., C:\\Users\\YourName\\OneDrive\\manga_folders): ").strip()
    
    # Prompt for .nomedia creation
    create_nomedia = input("Create .nomedia files for each series? (y/n): ").strip().lower() == 'y'
    
    if not os.path.isdir(source_dir):
        print(f"Error: Source directory '{source_dir}' does not exist.")
        logging.error(f"Source directory '{source_dir}' does not exist.")
        return
    
    try:
        print("Pausing OneDrive syncing is recommended to avoid errors. Ensure all files are fully synced (green checkmarks).")
        organize_manga_inplace(source_dir, create_nomedia)
        print(f"Successfully reorganized manga in {source_dir}")
        logging.info(f"Successfully reorganized manga in {source_dir}")
    except Exception as e:
        print(f"An error occurred: {e}")
        logging.error(f"Main process error: {e}")

if __name__ == "__main__":
    main()