import os
import hashlib

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

if __name__ == "__main__":
    folder = input("Enter folder path: ").strip()
    dups = find_duplicates(folder)

    if not dups:
        print("No duplicates found.")
    else:
        print("\nDuplicates:")
        for dup, original in dups:
            print(f"{dup} == {original}")
