#!/usr/bin/env python3
"""
TeraBox Downloader Script
Downloads files and folders from TeraBox share links without ads
"""

import os
import re
import json
import time
import requests
from urllib.parse import urlparse, parse_qs, unquote
from pathlib import Path
import argparse
import sys
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class TeraBoxDownloader:
    def __init__(self):
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        })
        
        # Set timeout for requests
        self.timeout = 30
        
    def extract_share_info(self, share_url):
        """Extract share information from TeraBox URL"""
        try:
            # Parse the URL to extract parameters
            parsed_url = urlparse(share_url)
            
            # Handle different TeraBox URL formats
            if 'terabox.com' in parsed_url.netloc or '1024terabox.com' in parsed_url.netloc:
                # Extract surl from URL
                if '/s/' in parsed_url.path:
                    surl = parsed_url.path.split('/s/')[-1]
                    # Remove any query parameters from surl
                    if '?' in surl:
                        surl = surl.split('?')[0]
                else:
                    query_params = parse_qs(parsed_url.query)
                    surl = query_params.get('surl', [None])[0]
                
                if surl:
                    return {'surl': surl, 'pwd': None, 'original_url': share_url}
            
            print(f"Could not extract share info from URL: {share_url}")
            return None
            
        except Exception as e:
            print(f"Error parsing URL: {e}")
            return None
    
    def get_file_list(self, share_info):
        """Get file list from share using multiple methods"""
        # Try multiple API endpoints
        endpoints = [
            "https://www.terabox.com/api/shorturlinfo",
            "https://1024terabox.com/api/shorturlinfo",
            "https://terabox.com/api/shorturlinfo"
        ]
        
        for api_url in endpoints:
            try:
                print(f"Trying API endpoint: {api_url}")
                
                params = {
                    'surl': share_info['surl'],
                    'pwd': share_info.get('pwd', ''),
                    'root': '1',
                    'fid': '',
                    'desc': '1',
                    'app_id': '250528'
                }
                
                response = self.session.get(api_url, params=params, timeout=self.timeout)
                response.raise_for_status()
                
                data = response.json()
                
                if data.get('errno') == 0:
                    file_list = data.get('list', [])
                    print(f"Successfully got file list from {api_url}")
                    return file_list
                else:
                    print(f"API Error from {api_url}: {data.get('errmsg', 'Unknown error')}")
                    continue
                    
            except requests.exceptions.ConnectionError as e:
                print(f"Connection error with {api_url}: {e}")
                continue
            except requests.exceptions.Timeout as e:
                print(f"Timeout error with {api_url}: {e}")
                continue
            except Exception as e:
                print(f"Error with {api_url}: {e}")
                continue
        
        # If all API endpoints fail, try web scraping approach
        print("All API endpoints failed, trying web scraping...")
        return self.get_file_list_web_scraping(share_info)
    
    def get_file_list_web_scraping(self, share_info):
        """Fallback method using web scraping"""
        try:
            # Try to access the share page directly
            share_url = share_info.get('original_url')
            print(f"Trying to scrape share page: {share_url}")
            
            response = self.session.get(share_url, timeout=self.timeout)
            response.raise_for_status()
            
            # Look for JSON data in the page
            content = response.text
            
            # Try to find file information in the page
            json_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', content, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(1))
                    # Extract file list from the data structure
                    # This is a simplified approach - may need adjustment based on actual page structure
                    if 'fileList' in data:
                        return data['fileList']
                except json.JSONDecodeError:
                    pass
            
            print("Could not extract file list from web page")
            return None
            
        except Exception as e:
            print(f"Web scraping error: {e}")
            return None
    
    def get_download_link(self, fs_id, share_info):
        """Get direct download link for a file"""
        endpoints = [
            "https://www.terabox.com/api/download",
            "https://1024terabox.com/api/download",
            "https://terabox.com/api/download"
        ]
        
        for api_url in endpoints:
            try:
                params = {
                    'surl': share_info['surl'],
                    'pwd': share_info.get('pwd', ''),
                    'fid': fs_id,
                    'app_id': '250528'
                }
                
                response = self.session.get(api_url, params=params, timeout=self.timeout)
                response.raise_for_status()
                
                data = response.json()
                
                if data.get('errno') == 0:
                    download_link = data.get('dlink')
                    return download_link
                else:
                    print(f"Error getting download link from {api_url}: {data.get('errmsg', 'Unknown error')}")
                    continue
                    
            except Exception as e:
                print(f"Error getting download link from {api_url}: {e}")
                continue
        
        return None
    
    def download_file(self, download_url, filename, output_dir):
        """Download a file from direct link"""
        try:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Sanitize filename
            filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
            
            # Full path for the file
            file_path = os.path.join(output_dir, filename)
            
            # Check if file already exists
            if os.path.exists(file_path):
                print(f"File already exists: {filename}")
                return True
            
            print(f"Downloading: {filename}")
            
            # Stream download to handle large files
            response = self.session.get(download_url, stream=True, timeout=self.timeout)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Show progress
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\rProgress: {percent:.1f}% ({downloaded}/{total_size} bytes)", end='')
                        else:
                            print(f"\rDownloaded: {downloaded} bytes", end='')
            
            print(f"\nCompleted: {filename}")
            return True
            
        except Exception as e:
            print(f"\nError downloading {filename}: {e}")
            # Clean up partial file
            if os.path.exists(file_path):
                os.remove(file_path)
            return False
    
    def download_from_share(self, share_url, output_dir="downloads"):
        """Main function to download from TeraBox share"""
        print(f"Processing TeraBox share: {share_url}")
        
        # Extract share information
        share_info = self.extract_share_info(share_url)
        if not share_info:
            print("Failed to extract share information")
            return False
        
        # Get file list
        file_list = self.get_file_list(share_info)
        if not file_list:
            print("Failed to get file list")
            return False
        
        print(f"Found {len(file_list)} items")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        success_count = 0
        
        for item in file_list:
            filename = item.get('server_filename', 'unknown')
            fs_id = item.get('fs_id')
            is_dir = item.get('isdir', 0)
            
            if is_dir:
                print(f"Skipping directory: {filename} (directory download not fully implemented)")
                continue
            
            # Get download link
            download_link = self.get_download_link(fs_id, share_info)
            if not download_link:
                print(f"Failed to get download link for: {filename}")
                continue
            
            # Download file
            if self.download_file(download_link, filename, output_dir):
                success_count += 1
            
            # Small delay to avoid rate limiting
            time.sleep(1)
        
        print(f"\nDownload completed: {success_count}/{len(file_list)} files downloaded")
        return success_count > 0

def main():
    parser = argparse.ArgumentParser(description='Download files from TeraBox share links')
    parser.add_argument('url', help='TeraBox share URL')
    parser.add_argument('-o', '--output', default='downloads', help='Output directory (default: downloads)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Create downloader instance
    downloader = TeraBoxDownloader()
    
    # Download from share
    success = downloader.download_from_share(args.url, args.output)
    
    if success:
        print(f"\nFiles downloaded to: {os.path.abspath(args.output)}")
    else:
        print("\nDownload failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
