#!/usr/bin/env python3
"""
Example script demonstrating different image conversion formats.
This script shows how to use the image converter programmatically.
"""

import os
import subprocess
import sys

def run_conversion(input_folder, output_folder, format_type, quality=85, lossless=False):
    """Run image conversion with specified parameters."""
    
    if not os.path.exists(input_folder):
        print(f"Input folder '{input_folder}' does not exist.")
        return False
    
    cmd = [
        sys.executable, 
        'image_converter.py',
        input_folder,
        output_folder,
        '-f', format_type,
        '-q', str(quality)
    ]
    
    if lossless and format_type == 'webp':
        cmd.append('--lossless')
    
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running conversion: {e}")
        return False

def main():
    """Main function demonstrating different conversions."""
    
    input_folder = "test_images"
    
    # Check if input folder exists
    if not os.path.exists(input_folder):
        print(f"Please create '{input_folder}' folder and add some images.")
        return
    
    print("Image Conversion Examples")
    print("=" * 30)
    
    # Example conversions
    conversions = [
        {
            'format': 'avif',
            'folder': 'avif_output',
            'quality': 85,
            'description': 'AVIF - Best compression for modern browsers'
        },
        {
            'format': 'webp',
            'folder': 'webp_output',
            'quality': 80,
            'description': 'WebP - Good compression with wide support'
        },
        {
            'format': 'webp',
            'folder': 'webp_lossless_output',
            'quality': 100,
            'lossless': True,
            'description': 'WebP Lossless - No quality loss'
        },
        {
            'format': 'png',
            'folder': 'png_output',
            'quality': 85,  # Quality doesn't affect PNG
            'description': 'PNG - Lossless, larger files'
        },
        {
            'format': 'jpeg',
            'folder': 'jpeg_output',
            'quality': 90,
            'description': 'JPEG - Universal compatibility'
        }
    ]
    
    for conversion in conversions:
        print(f"\nConverting to {conversion['description']}...")
        
        success = run_conversion(
            input_folder,
            conversion['folder'],
            conversion['format'],
            conversion.get('quality', 85),
            conversion.get('lossless', False)
        )
        
        if success:
            print(f"✓ Successfully converted to {conversion['format'].upper()}")
        else:
            print(f"✗ Failed to convert to {conversion['format'].upper()}")
    
    print("\nConversion examples completed!")
    print("Check the output folders to see the results.")

if __name__ == '__main__':
    main()
