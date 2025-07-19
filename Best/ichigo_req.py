import os
import sys
import subprocess
import urllib.request
import shutil

# --- CONFIGURATION ---
FONT_URL = "https://github.com/google/fonts/raw/main/ofl/mplus1/MPLUS1%5Bwght%5D.ttf"
FONT_FILENAME = "mangat.ttf"

TESSDATA_BEST_URL = "https://github.com/tesseract-ocr/tessdata_best/raw/main/"
LANG_FILES = ["jpn.traineddata", "jpn_vert.traineddata"]
TESSDATA_DIR = "tessdata"

REQUIRED_PACKAGES = [
    "opencv-python-headless",
    "numpy",
    "Pillow",
    "pytesseract",
    "deep-translator"
]

# --- HELPER FUNCTIONS ---

def check_command(command):
    """Check if a command exists on the system's PATH."""
    return shutil.which(command) is not None

def install_packages():
    """Install required Python packages using pip."""
    print("\n--- 🐍 Installing required Python packages... ---")
    try:
        for package in REQUIRED_PACKAGES:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print("✅ All Python packages installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR: Failed to install packages. Please try running 'pip install -r requirements.txt' manually.")
        print(f"Error details: {e}")
        sys.exit(1)

def download_file(url, destination):
    """Download a file from a URL to a destination, showing progress."""
    try:
        with urllib.request.urlopen(url) as response, open(destination, 'wb') as out_file:
            total_length = response.getheader('content-length')
            if total_length:
                total_length = int(total_length)
                print(f"Downloading {os.path.basename(destination)} ({total_length / 1024 / 1024:.2f} MB)")
                shutil.copyfileobj(response, out_file)
            else: # No content length header
                print(f"Downloading {os.path.basename(destination)}...")
                shutil.copyfileobj(response, out_file)
        print(f"✅ Downloaded {os.path.basename(destination)} successfully.")
    except Exception as e:
        print(f"❌ ERROR: Failed to download {url}. Please check your internet connection.")
        print(f"Error details: {e}")
        if os.path.exists(destination):
            os.remove(destination) # Clean up partial download
        sys.exit(1)

# --- MAIN SETUP LOGIC ---

def main():
    """Run the main setup process."""
    print("--- 🚀 Setting up Manga Translator Pro Environment ---")

    # 1. Check for Tesseract OCR
    print("\n--- 1. Checking for Tesseract OCR ---")
    if not check_command("tesseract"):
        print("⚠️ WARNING: Tesseract OCR is not found in your system's PATH.")
        print("Please install it from: https://github.com/tesseract-ocr/tesseract")
        print("\nAfter installation, make sure to:")
        print("  - On Windows: Add the Tesseract installation folder (e.g., 'C:\\Program Files\\Tesseract-OCR') to your system's PATH environment variable.")
        print("  - On macOS/Linux: It should be added to your PATH automatically by the installer (e.g., Homebrew, apt).")
        input("\nPress Enter to continue the setup once you have installed Tesseract...")
    else:
        print("✅ Tesseract OCR found.")

    # 2. Install Python packages
    install_packages()

    # 3. Download font file
    print(f"\n--- 2. Downloading Manga Font ({FONT_FILENAME}) ---")
    if not os.path.exists(FONT_FILENAME):
        download_file(FONT_URL, FONT_FILENAME)
    else:
        print(f"✅ Font file '{FONT_FILENAME}' already exists.")

    # 4. Download Tesseract language data
    print("\n--- 3. Downloading Tesseract Japanese Language Data ---")
    if not os.path.exists(TESSDATA_DIR):
        print(f"Creating directory: {TESSDATA_DIR}")
        os.makedirs(TESSDATA_DIR)

    for lang_file in LANG_FILES:
        dest_path = os.path.join(TESSDATA_DIR, lang_file)
        if not os.path.exists(dest_path):
            url = TESSDATA_BEST_URL + lang_file
            download_file(url, dest_path)
        else:
            print(f"✅ Language file '{lang_file}' already exists.")

    print("\n\n🎉 --- SETUP COMPLETE! --- 🎉")
    print("You are now ready to run the main translator script.")
    print("The script will automatically use the font and language files downloaded in this directory.")

if __name__ == "__main__":
    main()
