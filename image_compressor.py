#!/usr/bin/env python3
"""
Image compression script using mozjpeg.
Compresses all images in input folder and saves them to output folder.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from PIL import Image
import shutil

def check_mozjpeg():
    """Check if mozjpeg (cjpeg) is available in the system."""
    try:
        subprocess.run(['cjpeg', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def download_mozjpeg():
    """Download and setup mozjpeg for Windows."""
    print("For best results, you can download mozjpeg from:")
    print("https://github.com/mozilla/mozjpeg/releases")
    print("Extract cjpeg.exe to a folder in your PATH.")
    print("\nFor now, using standard JPEG optimization...")
    return False

def compress_image_with_mozjpeg(input_path, output_path, quality=85):
    """
    Compress an image using mozjpeg.
    
    Args:
        input_path: Path to input image
        output_path: Path to save compressed image
        quality: JPEG quality (1-100, default 85)
    """
    try:
        # Convert to JPEG if not already
        if not input_path.lower().endswith(('.jpg', '.jpeg')):
            # Convert to JPEG first using PIL
            with Image.open(input_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Save as temporary JPEG
                temp_path = str(output_path) + '.temp.jpg'
                img.save(temp_path, 'JPEG', quality=95)
                input_path = temp_path
        
        # Use mozjpeg to compress
        cmd = [
            'cjpeg',
            '-quality', str(quality),
            '-optimize',
            '-progressive',
            '-outfile', str(output_path),
            str(input_path)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        # Clean up temp file if created
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)
            
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error compressing {input_path}: {e}")
        return False
    except Exception as e:
        print(f"Error processing {input_path}: {e}")
        return False

def compress_with_pillow_optimized(input_path, output_path, quality=85):
    """
    Compress using PIL with optimization settings.
    """
    try:
        with Image.open(input_path) as img:
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Save with optimization
            img.save(
                output_path,
                'JPEG',
                quality=quality,
                optimize=True,
                progressive=True,
                # Additional optimization parameters
                subsampling=0,  # Better quality
                qtables='web_high'  # Optimized quantization tables
            )
        return True
    except Exception as e:
        print(f"Error compressing {input_path}: {e}")
        return False

def get_file_size(path):
    """Get file size in KB."""
    return os.path.getsize(path) / 1024

def compress_images_in_folder(input_folder, output_folder, quality=85):
    """
    Compress all images in input folder and save to output folder.
    
    Args:
        input_folder: Path to input folder containing images
        output_folder: Path to output folder for compressed images
        quality: JPEG quality (1-100, default 85)
    """
    input_path = Path(input_folder)
    output_path = Path(output_folder)
    
    # Create output folder if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Supported image formats
    supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp'}
    
    # Find all image files
    image_files = []
    for ext in supported_formats:
        image_files.extend(input_path.glob(f'*{ext}'))
        image_files.extend(input_path.glob(f'*{ext.upper()}'))
    
    if not image_files:
        print(f"No image files found in {input_folder}")
        return
    
    print(f"Found {len(image_files)} image files to compress...")
    
    total_original_size = 0
    total_compressed_size = 0
    successful_compressions = 0
    
    # Check if mozjpeg command line tool is available
    has_mozjpeg_cli = check_mozjpeg()
    
    for img_file in image_files:
        print(f"Processing: {img_file.name}")
        
        # Determine output filename (always .jpg for compressed output)
        output_filename = img_file.stem + '.jpg'
        output_file = output_path / output_filename
        
        # Get original file size
        original_size = get_file_size(img_file)
        total_original_size += original_size
        
        # Compress the image
        success = False
        if has_mozjpeg_cli:
            success = compress_image_with_mozjpeg(img_file, output_file, quality)
        else:
            success = compress_with_pillow_optimized(img_file, output_file, quality)
        
        if success:
            compressed_size = get_file_size(output_file)
            total_compressed_size += compressed_size
            successful_compressions += 1
            
            # Calculate compression ratio
            compression_ratio = (1 - compressed_size / original_size) * 100
            print(f"  ✓ {original_size:.1f}KB → {compressed_size:.1f}KB ({compression_ratio:.1f}% reduction)")
        else:
            print(f"  ✗ Failed to compress {img_file.name}")
    
    # Print summary
    print(f"\n--- Compression Summary ---")
    print(f"Images processed: {len(image_files)}")
    print(f"Successful compressions: {successful_compressions}")
    print(f"Total original size: {total_original_size:.1f}KB")
    print(f"Total compressed size: {total_compressed_size:.1f}KB")
    
    if total_original_size > 0:
        overall_reduction = (1 - total_compressed_size / total_original_size) * 100
        print(f"Overall size reduction: {overall_reduction:.1f}%")

def main():
    parser = argparse.ArgumentParser(description='Compress images using mozjpeg')
    parser.add_argument('input_folder', help='Path to input folder containing images')
    parser.add_argument('output_folder', help='Path to output folder for compressed images')
    parser.add_argument('-q', '--quality', type=int, default=85, 
                       help='JPEG quality (1-100, default: 85)')
    
    args = parser.parse_args()
    
    # Validate input folder
    if not os.path.exists(args.input_folder):
        print(f"Error: Input folder '{args.input_folder}' does not exist.")
        sys.exit(1)
    
    # Check if mozjpeg is available
    if not check_mozjpeg():
        print("mozjpeg (cjpeg) not found.")
        download_mozjpeg()
        print("Warning: Using PIL for compression instead of mozjpeg.")
        print("For best results, install mozjpeg manually.")
    
    # Compress images
    compress_images_in_folder(args.input_folder, args.output_folder, args.quality)

if __name__ == '__main__':
    # If no command line arguments, use interactive mode
    if len(sys.argv) == 1:
        print("Image Compression Tool using mozjpeg")
        print("=" * 40)
        
        input_folder = input("Enter input folder path: ").strip()
        output_folder = input("Enter output folder path: ").strip()
        
        quality_input = input("Enter JPEG quality (1-100, default 85): ").strip()
        quality = 85 if not quality_input else int(quality_input)
        
        if not os.path.exists(input_folder):
            print(f"Error: Input folder '{input_folder}' does not exist.")
            sys.exit(1)
        
        # Check if mozjpeg is available
        if not check_mozjpeg():
            print("mozjpeg (cjpeg) not found.")
            download_mozjpeg()
            print("Warning: Using PIL for compression instead of mozjpeg.")
            print("For best results, install mozjpeg manually.")
        
        compress_images_in_folder(input_folder, output_folder, quality)
    else:
        main()
