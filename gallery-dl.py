#!/usr/bin/env python3
import subprocess
import time
import json
import os
from pathlib import Path

# Configuration file path for Windows
CONFIG_PATH = str(Path.home() / "gallery-dl" / "config.json")

# Ensure configuration file exists
def create_config():
    config = {
        "extractor": {
            "deviantart": {
                "client-id": "5388",  # Default client-id from OAuth setup
                "client-secret": "",  # Leave blank unless provided by DeviantArt
                "refresh-token": "2bf362643743c933f315bb9902832430cbad64fa",  # Your refresh-token
                "include": "gallery,scraps",
                "wait-min": 3,  # Increased wait time to avoid 429 errors
                "retries": 5,   # Number of retries for failed requests
                "sleep-request": 3.0  # Sleep time between API requests
            },
            "pinterest": {
                "cookies": str(Path.home() / "cookies.txt"),  # Update with actual path to cookies.txt
                "retries": 5,
                "sleep-request": 3.0
            }
        },
        "downloader": {
            "retries": 5,
            "timeout": 30.0,
            "sleep": 3.0
        }
    }
    
    # Create config directory if it doesn't exist
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    
    # Write config file
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=4)
    print(f"Configuration file created at {CONFIG_PATH}")

# Function to run gallery-dl command with retry mechanism
def run_gallery_dl(url, max_retries=3, initial_delay=3):
    for attempt in range(max_retries):
        try:
            # Run gallery-dl command
            result = subprocess.run(
                ["gallery-dl", "--config", CONFIG_PATH, url],
                capture_output=True,
                text=True,
                check=True
            )
            print(result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            if "429 Too Many Requests" in e.stderr:
                delay = initial_delay * (2 ** attempt)  # Exponential backoff
                print(f"429 Too Many Requests detected. Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print(f"Error: {e.stderr}")
                return False
    print(f"Failed to download from {url} after {max_retries} attempts.")
    return False

def main():
    # Check if config file exists, create if it doesn't
    if not os.path.exists(CONFIG_PATH):
        print("Configuration file not found. Creating a default one.")
        create_config()
    
    # Example URLs to download
    urls = [
        "https://www.deviantart.com/fdpdablizzard998/gallery/all"
    ]
    
    # Download from each URL
    for url in urls:
        print(f"Downloading from {url}")
        success = run_gallery_dl(url)
        if not success:
            print(f"Failed to download from {url}")

if __name__ == "__main__":
    main()