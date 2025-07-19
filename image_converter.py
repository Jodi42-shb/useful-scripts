#!/usr/bin/env python3
"""
Multi-format image converter supporting AVIF, WebP, PNG, and JPEG.
Converts all images in input folder to the specified format and saves them to output folder.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from PIL import Image
import pillow_heif

# Register HEIF opener with Pillow for AVIF support
pillow_heif.register_heif_opener()

def check_dependencies():
    """Check if required packages are installed."""
    missing_packages = []
    
    try:
        import pillow_heif
    except ImportError:
        missing_packages.append('pillow-heif')
    
    return missing_packages

def install_dependencies():
    """Install missing dependencies."""
    missing = check_dependencies()
    if missing:
        print(f"Installing missing dependencies: {', '.join(missing)}")
        try:
            for package in missing:
                subprocess.run([sys.executable, '-m', 'pip', 'install', package], check=True)
            print("Dependencies installed successfully!")
            return True
        except subprocess.CalledProcessError:
            print("Failed to install dependencies. Please install manually:")
            for package in missing:
                print(f"  pip install {package}")
            return False
    return True

def convert_to_avif(input_path, output_path, quality=85):
    """
    Convert image to AVIF format.
    
    Args:
        input_path: Path to input image
        output_path: Path to save converted image
        quality: AVIF quality (1-100, default 85)
    """
    try:
        with Image.open(input_path) as img:
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Save as AVIF
            img.save(
                output_path,
                'AVIF',
                quality=quality,
                speed=6,  # Compression speed vs quality tradeoff (0-10)
            )
        return True
    except Exception as e:
        print(f"Error converting {input_path} to AVIF: {e}")
        return False

def convert_to_webp(input_path, output_path, quality=85, lossless=False):
    """
    Convert image to WebP format.
    
    Args:
        input_path: Path to input image
        output_path: Path to save converted image
        quality: WebP quality (1-100, default 85)
        lossless: Use lossless compression
    """
    try:
        with Image.open(input_path) as img:
            # Convert to RGB if necessary (unless lossless and has alpha)
            if img.mode == 'RGBA' and lossless:
                pass  # Keep RGBA for lossless WebP
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Save as WebP
            img.save(
                output_path,
                'WebP',
                quality=quality if not lossless else 100,
                lossless=lossless,
                method=6,  # Compression method (0-6, 6 is slowest but best)
            )
        return True
    except Exception as e:
        print(f"Error converting {input_path} to WebP: {e}")
        return False

def convert_to_png(input_path, output_path, optimize=True):
    """
    Convert image to PNG format.
    
    Args:
        input_path: Path to input image
        output_path: Path to save converted image
        optimize: Use PNG optimization
    """
    try:
        with Image.open(input_path) as img:
            # PNG supports RGBA, so preserve transparency
            if img.mode == 'P':
                img = img.convert('RGBA')
            
            # Save as PNG
            img.save(
                output_path,
                'PNG',
                optimize=optimize,
                compress_level=9,  # Maximum compression
            )
        return True
    except Exception as e:
        print(f"Error converting {input_path} to PNG: {e}")
        return False

def convert_to_jpeg(input_path, output_path, quality=85):
    """
    Convert image to JPEG format.
    
    Args:
        input_path: Path to input image
        output_path: Path to save converted image
        quality: JPEG quality (1-100, default 85)
    """
    try:
        with Image.open(input_path) as img:
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Save as JPEG
            img.save(
                output_path,
                'JPEG',
                quality=quality,
                optimize=True,
                progressive=True,
                subsampling=0,  # Better quality
                qtables='web_high'  # Optimized quantization tables
            )
        return True
    except Exception as e:
        print(f"Error converting {input_path} to JPEG: {e}")
        return False

def get_file_size(path):
    """Get file size in KB."""
    return os.path.getsize(path) / 1024

def convert_images_in_folder(input_folder, output_folder, output_format, quality=85, lossless=False):
    """
    Convert all images in input folder to specified format and save to output folder.
    
    Args:
        input_folder: Path to input folder containing images
        output_folder: Path to output folder for converted images
        output_format: Output format ('avif', 'webp', 'png', 'jpeg')
        quality: Image quality (1-100, default 85)
        lossless: Use lossless compression (WebP only)
    """
    input_path = Path(input_folder)
    output_path = Path(output_folder)
    
    # Create output folder if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Supported input formats
    supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp', '.avif'}
    
    # Find all image files
    image_files = []
    for ext in supported_formats:
        image_files.extend(input_path.glob(f'*{ext}'))
        image_files.extend(input_path.glob(f'*{ext.upper()}'))
    
    if not image_files:
        print(f"No image files found in {input_folder}")
        return
    
    print(f"Found {len(image_files)} image files to convert to {output_format.upper()}...")
    
    # Format-specific settings
    format_extensions = {
        'avif': '.avif',
        'webp': '.webp',
        'png': '.png',
        'jpeg': '.jpg'
    }
    
    conversion_functions = {
        'avif': convert_to_avif,
        'webp': convert_to_webp,
        'png': convert_to_png,
        'jpeg': convert_to_jpeg
    }
    
    total_original_size = 0
    total_converted_size = 0
    successful_conversions = 0
    
    for img_file in image_files:
        print(f"Processing: {img_file.name}")
        
        # Determine output filename
        output_filename = img_file.stem + format_extensions[output_format]
        output_file = output_path / output_filename
        
        # Get original file size
        original_size = get_file_size(img_file)
        total_original_size += original_size
        
        # Convert the image
        success = False
        convert_func = conversion_functions[output_format]
        
        if output_format == 'webp':
            success = convert_func(img_file, output_file, quality, lossless)
        elif output_format == 'png':
            success = convert_func(img_file, output_file, True)
        else:
            success = convert_func(img_file, output_file, quality)
        
        if success:
            converted_size = get_file_size(output_file)
            total_converted_size += converted_size
            successful_conversions += 1
            
            # Calculate size change
            size_change = (1 - converted_size / original_size) * 100
            change_symbol = "↓" if size_change > 0 else "↑"
            print(f"  ✓ {original_size:.1f}KB → {converted_size:.1f}KB ({change_symbol}{abs(size_change):.1f}%)")
        else:
            print(f"  ✗ Failed to convert {img_file.name}")
    
    # Print summary
    print(f"\n--- Conversion Summary ---")
    print(f"Images processed: {len(image_files)}")
    print(f"Successful conversions: {successful_conversions}")
    print(f"Total original size: {total_original_size:.1f}KB")
    print(f"Total converted size: {total_converted_size:.1f}KB")
    
    if total_original_size > 0:
        overall_change = (1 - total_converted_size / total_original_size) * 100
        change_type = "reduction" if overall_change > 0 else "increase"
        print(f"Overall size {change_type}: {abs(overall_change):.1f}%")

def main():
    parser = argparse.ArgumentParser(description='Convert images to different formats')
    parser.add_argument('input_folder', help='Path to input folder containing images')
    parser.add_argument('output_folder', help='Path to output folder for converted images')
    parser.add_argument('-f', '--format', choices=['avif', 'webp', 'png', 'jpeg'], 
                       default='webp', help='Output format (default: webp)')
    parser.add_argument('-q', '--quality', type=int, default=85, 
                       help='Image quality (1-100, default: 85)')
    parser.add_argument('--lossless', action='store_true', 
                       help='Use lossless compression (WebP only)')
    
    args = parser.parse_args()
    
    # Validate input folder
    if not os.path.exists(args.input_folder):
        print(f"Error: Input folder '{args.input_folder}' does not exist.")
        sys.exit(1)
    
    # Check and install dependencies
    if not install_dependencies():
        print("Cannot proceed without required dependencies.")
        sys.exit(1)
    
    # Convert images
    convert_images_in_folder(
        args.input_folder, 
        args.output_folder, 
        args.format, 
        args.quality, 
        args.lossless
    )

if __name__ == '__main__':
    # If no command line arguments, use interactive mode
    if len(sys.argv) == 1:
        print("Multi-Format Image Converter")
        print("=" * 30)
        
        input_folder = input("Enter input folder path: ").strip()
        output_folder = input("Enter output folder path: ").strip()
        
        print("\nAvailable formats:")
        print("1. AVIF (most efficient, modern browsers)")
        print("2. WebP (good compression, wide support)")
        print("3. PNG (lossless, large files)")
        print("4. JPEG (lossy, universal support)")
        
        format_choice = input("Choose format (1-4): ").strip()
        format_map = {'1': 'avif', '2': 'webp', '3': 'png', '4': 'jpeg'}
        output_format = format_map.get(format_choice, 'webp')
        
        if output_format in ['avif', 'webp', 'jpeg']:
            quality_input = input(f"Enter quality (1-100, default 85): ").strip()
            quality = 85 if not quality_input else int(quality_input)
        else:
            quality = 85
        
        lossless = False
        if output_format == 'webp':
            lossless_input = input("Use lossless compression? (y/n, default n): ").strip().lower()
            lossless = lossless_input == 'y'
        
        if not os.path.exists(input_folder):
            print(f"Error: Input folder '{input_folder}' does not exist.")
            sys.exit(1)
        
        # Check and install dependencies
        if not install_dependencies():
            print("Cannot proceed without required dependencies.")
            sys.exit(1)
        
        convert_images_in_folder(input_folder, output_folder, output_format, quality, lossless)
    else:
        main()
