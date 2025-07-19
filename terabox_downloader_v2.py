#!/usr/bin/env python3
"""
TeraBox Downloader V2 - Alternative approach
Downloads files from TeraBox share links using different methods
"""

import os
import re
import json
import time
import requests
from urllib.parse import urlparse, parse_qs, unquote
import argparse
import sys
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import base64

class TeraBoxDownloaderV2:
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
        
        # Use different headers that might work better
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://1024terabox.com/',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1'
        })
        
        self.timeout = 30
        
        # Disable SSL verification for TeraBox CDN domains
        self.verify_ssl = False
        
    def extract_share_info(self, share_url):
        """Extract share information from TeraBox URL"""
        try:
            parsed_url = urlparse(share_url)
            
            if 'terabox.com' in parsed_url.netloc or '1024terabox.com' in parsed_url.netloc:
                if '/s/' in parsed_url.path:
                    surl = parsed_url.path.split('/s/')[-1]
                    if '?' in surl:
                        surl = surl.split('?')[0]
                    
                    # Also extract domain for later use
                    domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
                    
                    return {
                        'surl': surl, 
                        'pwd': None, 
                        'original_url': share_url,
                        'domain': domain
                    }
            
            print(f"Could not extract share info from URL: {share_url}")
            return None
            
        except Exception as e:
            print(f"Error parsing URL: {e}")
            return None
    
    def get_file_list_direct(self, share_info):
        """Try to get file list by accessing the share page directly"""
        try:
            share_url = share_info['original_url']
            domain = share_info['domain']
            
            print(f"Accessing share page: {share_url}")
            
            # Try to get the page
            response = self.session.get(share_url, timeout=self.timeout, verify=self.verify_ssl)
            response.raise_for_status()
            
            content = response.text
            
            # Look for various JSON data patterns in the page
            patterns = [
                r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
                r'locals\.mset\s*\(\s*({.*?})\s*\)',
                r'window\.yunData\s*=\s*({.*?});',
                r'"file_list":\s*(\[.*?\])',
                r'"list":\s*(\[.*?\])'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content, re.DOTALL)
                for match in matches:
                    try:
                        if match.strip().startswith('['):
                            # Direct file list
                            data = json.loads(match)
                            if isinstance(data, list) and len(data) > 0:
                                return data
                        else:
                            # JSON object
                            data = json.loads(match)
                            
                            # Try different paths to file list
                            file_list_paths = [
                                ['file_list'],
                                ['list'],
                                ['data', 'file_list'],
                                ['data', 'list'],
                                ['shareData', 'file_list'],
                                ['shareData', 'list']
                            ]
                            
                            for path in file_list_paths:
                                current = data
                                for key in path:
                                    if isinstance(current, dict) and key in current:
                                        current = current[key]
                                    else:
                                        break
                                else:
                                    if isinstance(current, list) and len(current) > 0:
                                        return current
                    except json.JSONDecodeError:
                        continue
            
            # If JSON parsing fails, try to extract download links directly
            print("Could not find JSON data, trying direct link extraction...")
            return self.extract_direct_links(content, share_info)
            
        except Exception as e:
            print(f"Error accessing share page: {e}")
            return None
    
    def extract_direct_links(self, content, share_info):
        """Extract download links directly from page content"""
        try:
            # Look for download links in the HTML
            download_patterns = [
                r'href="(https?://[^"]*download[^"]*)"',
                r'"(https?://[^"]*\.(?:zip|rar|7z|tar|gz|mp4|avi|mkv|pdf|doc|docx|xls|xlsx|ppt|pptx|jpg|jpeg|png|gif)[^"]*)"',
                r'data-url="([^"]*)"',
                r'"dlink":"([^"]*)"'
            ]
            
            files = []
            for pattern in download_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    # Clean up the URL
                    clean_url = match.replace('\\/', '/').replace('\\', '')
                    if clean_url.startswith('http'):
                        # Extract filename from URL
                        filename = os.path.basename(urlparse(clean_url).path)
                        if filename:
                            files.append({
                                'server_filename': filename,
                                'dlink': clean_url,
                                'fs_id': f'direct_{len(files)}',
                                'isdir': 0
                            })
            
            return files if files else None
            
        except Exception as e:
            print(f"Error extracting direct links: {e}")
            return None
    
    def try_api_with_session(self, share_info):
        """Try API calls with session cookies"""
        try:
            # First, visit the share page to get cookies
            share_url = share_info['original_url']
            response = self.session.get(share_url, timeout=self.timeout, verify=self.verify_ssl)
            response.raise_for_status()
            
            # Now try API calls with the session cookies
            api_endpoints = [
                f"{share_info['domain']}/api/shorturlinfo",
                f"{share_info['domain']}/share/list",
                f"{share_info['domain']}/api/list"
            ]
            
            for api_url in api_endpoints:
                try:
                    params = {
                        'surl': share_info['surl'],
                        'pwd': share_info.get('pwd', ''),
                        'root': '1',
                        'fid': '',
                        'desc': '1',
                        'app_id': '250528'
                    }
                    
                    response = self.session.get(api_url, params=params, timeout=self.timeout, verify=self.verify_ssl)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('errno') == 0 and 'list' in data:
                            return data['list']
                except Exception as e:
                    print(f"API {api_url} failed: {e}")
                    continue
                    
        except Exception as e:
            print(f"Session API attempt failed: {e}")
            
        return None
    
    def download_file(self, file_info, output_dir):
        """Download a file"""
        try:
            filename = file_info.get('server_filename', 'unknown_file')
            download_url = file_info.get('dlink')
            
            if not download_url:
                print(f"No download URL for {filename}")
                return False
            
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Sanitize filename
            filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
            file_path = os.path.join(output_dir, filename)
            
            # Check if file already exists
            if os.path.exists(file_path):
                print(f"File already exists: {filename}")
                return True
            
            print(f"Downloading: {filename}")
            print(f"URL: {download_url}")
            
            # Try to download
            response = self.session.get(download_url, stream=True, timeout=self.timeout, verify=self.verify_ssl)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\rProgress: {percent:.1f}%", end='')
                        else:
                            print(f"\rDownloaded: {downloaded} bytes", end='')
            
            print(f"\nCompleted: {filename}")
            return True
            
        except Exception as e:
            print(f"\nError downloading {filename}: {e}")
            if os.path.exists(file_path):
                os.remove(file_path)
            return False
    
    def download_from_share(self, share_url, output_dir="downloads"):
        """Main download function"""
        print(f"Processing TeraBox share: {share_url}")
        
        # Extract share info
        share_info = self.extract_share_info(share_url)
        if not share_info:
            return False
        
        # Try different methods to get file list
        file_list = None
        
        # Method 1: Direct page access
        file_list = self.get_file_list_direct(share_info)
        
        # Method 2: Try API with session
        if not file_list:
            print("Trying API with session...")
            file_list = self.try_api_with_session(share_info)
        
        if not file_list:
            print("All methods failed to get file list")
            return False
        
        print(f"Found {len(file_list)} items")
        
        # Download files
        success_count = 0
        for item in file_list:
            if item.get('isdir', 0):
                print(f"Skipping directory: {item.get('server_filename', 'unknown')}")
                continue
            
            if self.download_file(item, output_dir):
                success_count += 1
            
            time.sleep(1)  # Rate limiting
        
        print(f"\nDownload completed: {success_count}/{len(file_list)} files")
        return success_count > 0

def main():
    parser = argparse.ArgumentParser(description='TeraBox Downloader V2')
    parser.add_argument('url', help='TeraBox share URL')
    parser.add_argument('-o', '--output', default='downloads', help='Output directory')
    
    args = parser.parse_args()
    
    downloader = TeraBoxDownloaderV2()
    success = downloader.download_from_share(args.url, args.output)
    
    if success:
        print(f"\nFiles downloaded to: {os.path.abspath(args.output)}")
    else:
        print("\nDownload failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
