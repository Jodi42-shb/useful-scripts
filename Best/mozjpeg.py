import os
import subprocess
from PIL import Image
import mozjpeg_lossless_optimization
from io import BytesIO
import shutil

def compress_image(input_path, output_path, quality=85, preserve_metadata=True):
    """
    Compress a single image using MozJPEG.
    Supports JPEG and PNG inputs, outputs JPEG.
    """
    try:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Open image with Pillow
        with Image.open(input_path) as img:
            # Convert to RGB if necessary (handles PNG with alpha)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Save to BytesIO for MozJPEG processing
            jpeg_io = BytesIO()
            img.save(jpeg_io, format='JPEG', quality=quality, optimize=True)
            jpeg_io.seek(0)
            jpeg_bytes = jpeg_io.read()
            
            # Apply MozJPEG lossless optimization
            copy_option = mozjpeg_lossless_optimization.COPY_MARKERS.ALL if preserve_metadata else mozjpeg_lossless_optimization.COPY_MARKERS.NONE
            optimized_jpeg_bytes = mozjpeg_lossless_optimization.optimize(jpeg_bytes, copy=copy_option)
            
            # Write optimized JPEG to output path
            with open(output_path, 'wb') as output_file:
                output_file.write(optimized_jpeg_bytes)
                
            print(f"Compressed: {input_path} -> {output_path}")
            
    except Exception as e:
        print(f"Error compressing {input_path}: {str(e)}")

def compress_folder(input_dir, output_dir, quality=85, preserve_metadata=True):
    """
    Recursively compress all JPEG and PNG images in input_dir, saving to output_dir.
    """
    # Supported image extensions
    valid_extensions = ('.jpg', '.jpeg', '.png')
    
    # Walk through input directory
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(valid_extensions):
                input_path = os.path.join(root, file)
                # Compute relative path and output path
                rel_path = os.path.relpath(input_path, input_dir)
                output_path = os.path.join(output_dir, os.path.splitext(rel_path)[0] + '.jpg')
                
                compress_image(input_path, output_path, quality, preserve_metadata)

def main():
    # Define input and output directories
    input_dir = 'input_images'  # Change to your input folder path
    output_dir = 'compressed_images'  # Change to your output folder path
    quality = 85  # Adjust quality (0-100, higher means better quality but larger files)
    preserve_metadata = True  # Set to False to strip metadata
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print(f"Compressing images in {input_dir}...")
    compress_folder(input_dir, output_dir, quality, preserve_metadata)
    print("Compression complete.")

if __name__ == "__main__":
    main()