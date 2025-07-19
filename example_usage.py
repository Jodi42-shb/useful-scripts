#!/usr/bin/env python3
"""
Example usage of TeraBox Downloader
"""

from terabox_downloader import TeraBoxDownloader

def main():
    # Create downloader instance
    downloader = TeraBoxDownloader()
    
    # Example TeraBox share URL (replace with your actual URL)
    share_url = "https://www.terabox.com/s/1AbCdEfGhIjKlMnOpQrStUvWxYz"
    
    # Download to current directory in 'downloads' folder
    output_directory = "downloads"
    
    print("Starting TeraBox download...")
    success = downloader.download_from_share(share_url, output_directory)
    
    if success:
        print(f"Download completed successfully! Files saved to: {output_directory}")
    else:
        print("Download failed!")

if __name__ == "__main__":
    main()
