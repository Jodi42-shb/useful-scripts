import os
import glob
import ffmpeg
from tqdm import tqdm
import re

def validate_ffmpeg():
    """Check if FFmpeg is installed and supports AV1."""
    try:
        probe = ffmpeg.probe.__module__  # Check if ffmpeg-python is available
        stream = os.popen('ffmpeg -encoders')
        encoders = stream.read()
        if 'libsvtav1' in encoders:
            return 'libsvtav1'
        elif 'libaom-av1' in encoders:
            return 'libaom-av1'
        else:
            raise Exception("No AV1 encoder (libsvtav1 or libaom-av1) found in FFmpeg.")
    except Exception as e:
        print(f"Error: FFmpeg not installed or AV1 not supported. Install FFmpeg with AV1 support. {e}")
        exit(1)

def get_crop_dimensions(input_file):
    """Detect black bars using cropdetect and return crop filter string."""
    try:
        stream = ffmpeg.input(input_file).filter('cropdetect', limit=0, round=2).output('-', format='null').run(capture_stderr=True, quiet=True)
        stderr = stream[1].decode('utf-8')
        crop_line = [line for line in stderr.split('\n') if 'crop=' in line][-1]
        crop_params = re.search(r'crop=(\d+:\d+:\d+:\d+)', crop_line)
        if crop_params:
            return f"crop={crop_params.group(1)}"
        else:
            return None
    except Exception as e:
        print(f"Warning: Could not detect crop for {input_file}. Skipping crop. {e}")
        return None

def convert_video(input_file, output_file, encoder, preset, crf, crop=False):
    """Convert a single video to AV1 with specified settings."""
    try:
        stream = ffmpeg.input(input_file)
        if crop:
            crop_filter = get_crop_dimensions(input_file)
            if crop_filter:
                stream = stream.filter('crop', *crop_filter.split(':'))
        stream = stream.output(
            output_file,
            vcodec=encoder,
            preset=preset,
            crf=crf,
            acodec='copy',
            format='matroska'
        )
        stream.run(quiet=False, overwrite_output=True)
        print(f"Successfully converted {input_file} to {output_file}")
    except ffmpeg.Error as e:
        print(f"Error converting {input_file}: {e.stderr.decode('utf-8')}")
    except Exception as e:
        print(f"Unexpected error converting {input_file}: {e}")

def main():
    print("AV1 Video Converter")
    encoder = validate_ffmpeg()
    print(f"Using encoder: {encoder}")
    
    # Choose encoding mode
    mode = input("Choose mode: (1) Single file, (2) Batch folder: ").strip()
    while mode not in ['1', '2']:
        print("Invalid choice. Enter 1 or 2.")
        mode = input("Choose mode: (1) Single file, (2) Batch folder: ").strip()

    # Get quality settings
    if encoder == 'libsvtav1':
        preset_range = range(1, 14)
        preset_prompt = "Enter preset (1-13, higher is faster, e.g., 8 for speed): "
    else:
        preset_range = range(0, 9)
        preset_prompt = "Enter preset (0-8, higher is faster, e.g., 6 for speed): "
    
    preset = input(preset_prompt).strip()
    while not preset.isdigit() or int(preset) not in preset_range:
        print(f"Invalid preset. Choose {min(preset_range)}-{max(preset_range)}.")
        preset = input(preset_prompt).strip()
    preset = int(preset)

    crf = input("Enter CRF (0-63, higher is faster/lower quality, e.g., 30): ").strip()
    while not crf.isdigit() or int(crf) < 0 or int(crf) > 63:
        print("Invalid CRF. Choose 0-63.")
        crf = input("Enter CRF (0-63, higher is faster/lower quality, e.g., 30): ").strip()
    crf = int(crf)

    crop = input("Enable automatic black bar cropping? (y/n): ").strip().lower() == 'y'

    # Process input
    if mode == '1':
        input_file = input("Enter input video file path: ").strip()
        while not os.path.isfile(input_file):
            print("File not found.")
            input_file = input("Enter input video file path: ").strip()
        output_file = os.path.splitext(input_file)[0] + '_av1.mkv'
        convert_video(input_file, output_file, encoder, preset, crf, crop)
    else:
        folder = input("Enter folder path containing videos: ").strip()
        while not os.path.isdir(folder):
            print("Folder not found.")
            folder = input("Enter folder path containing videos: ").strip()
        
        video_extensions = ['*.mp4', '*.mkv', '*.avi', '*.mov', '*.wmv']
        files = []
        for ext in video_extensions:
            files.extend(glob.glob(os.path.join(folder, ext)))
        
        if not files:
            print("No video files found in folder.")
            return
        
        print(f"Found {len(files)} video(s) to convert.")
        for input_file in tqdm(files, desc="Converting videos"):
            output_file = os.path.splitext(input_file)[0] + '_av1.mkv'
            convert_video(input_file, output_file, encoder, preset, crf, crop)

if __name__ == '__main__':
    main()