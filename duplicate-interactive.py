#!/usr/bin/env python3
import os
import hashlib
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

def file_info(path):
    size = os.path.getsize(path) / (1024 * 1024)
    return f"{path} ({size:.2f} MB)"

def interactive_cleanup(dups):
    for i, (dup, original) in enumerate(dups, 1):
        print(f"\n[{i}] Duplicate found:")
        print("1:", file_info(original))
        print("2:", file_info(dup))

        print("\nOptions:")
        print("1 -> keep 1, trash 2")
        print("2 -> keep 2, trash 1")
        print("s -> skip")
        print("q -> quit")

        choice = input("Your choice: ").strip().lower()

        if choice == "1":
            send2trash(dup)
            print("→ Sent to trash:", dup)

        elif choice == "2":
            send2trash(original)
            print("→ Sent to trash:", original)

        elif choice == "q":
            print("Stopping...")
            break

        else:
            print("Skipped")

if __name__ == "__main__":
    folder = input("Enter folder ('.' for current): ").strip()

    dups = find_duplicates(folder)

    if not dups:
        print("No duplicates found.")
    else:
        interactive_cleanup(dups)
