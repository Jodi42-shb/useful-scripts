#!/usr/bin/env python3
import os
import hashlib
import shutil
from send2trash import send2trash

def get_hash(file_path, chunk_size=8192):
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()

def find_duplicates(folder):
    hashes = {}
    duplicates = []

    for root, _, files in os.walk(folder):
        for file in files:
            path = os.path.join(root, file)
            try:
                file_hash = get_hash(path)
                if file_hash in hashes:
                    duplicates.append((path, hashes[file_hash]))
                else:
                    hashes[file_hash] = path
            except Exception as e:
                print(f"Error reading {path}: {e}")

    return duplicates

def handle_duplicates(dups, action, base_folder):
    dup_folder = os.path.join(base_folder, "duplicates")
    os.makedirs(dup_folder, exist_ok=True)

    for dup, original in dups:
        try:
            if action == "delete":
                os.remove(dup)
                print(f"Deleted: {dup}")

            elif action == "move":
                dest = os.path.join(dup_folder, os.path.basename(dup))
                shutil.move(dup, dest)
                print(f"Moved: {dup} -> {dest}")

            elif action == "trash":
                send2trash(dup)
                print(f"Sent to trash: {dup}")

            elif action == "skip":
                pass

        except Exception as e:
            print(f"Error handling {dup}: {e}")

if __name__ == "__main__":
    folder = input("Enter folder path ('.' for current): ").strip()

    dups = find_duplicates(folder)

    if not dups:
        print("No duplicates found.")
        exit()

    print("\nDuplicates found:")
    for dup, original in dups:
        print(f"{dup} == {original}")

    print("\nWhat do you want to do?")
    print("1. Delete duplicates")
    print("2. Move to 'duplicates' folder")
    print("3. Send to trash")
    print("4. Do nothing")

    choice = input("Enter choice (1/2/3/4): ").strip()

    if choice == "1":
        handle_duplicates(dups, "delete", folder)
    elif choice == "2":
        handle_duplicates(dups, "move", folder)
    elif choice == "3":
        handle_duplicates(dups, "trash", folder)
    else:
        print("No action taken.")
