import os
from PIL import Image, ImageDraw, ImageFont
import pytesseract
import translators as ts
import cv2
import numpy as np

# --- IMPORTANT SETUP ---
# On Windows, you might need to set the path to the Tesseract executable.
# Uncomment the line below and change the path to where you installed Tesseract.
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def get_clean_directory_path(prompt):
    """Gets a directory path from the user and validates it."""
    while True:
        path = input(prompt).strip().replace('"', '').replace("'", "")
        if os.path.isdir(path):
            return path
        else:
            print("Error: The specified path does not exist or is not a directory. Please try again.")

def get_font_path(prompt):
    """Gets a font file path from the user and validates it."""
    while True:
        path = input(prompt).strip().replace('"', '').replace("'", "")
        if os.path.isfile(path) and path.lower().endswith(('.ttf', '.otf')):
            return path
        else:
            print("Error: The specified path is not a valid .ttf or .otf font file. Please try again.")

def translate_and_draw(image_path, dest_path, font_path, lang='jpn'):
    """
    Processes a single manga image: detects text, translates it, and redraws it on the image.

    Args:
        image_path (str): The full path to the source image.
        dest_path (str): The full path to save the translated image.
        font_path (str): Path to the .ttf font file for drawing text.
        lang (str): The language code for Tesseract to detect (e.g., 'jpn' for Japanese).
    """
    try:
        # --- 1. Load the Image ---
        img = Image.open(image_path)
        img_cv = cv2.imread(image_path) # OpenCV is used for more robust text box detection

        # --- 2. Use Tesseract to get OCR data including bounding boxes ---
        # We get detailed data to know WHERE the text is.
        print(f"    -> Finding text blocks...")
        ocr_data = pytesseract.image_to_data(img, lang=lang, output_type=pytesseract.Output.DICT)

        n_boxes = len(ocr_data['level'])
        if n_boxes <= 1:
            print("    -> No text found to translate.")
            img.save(dest_path)
            return

        draw = ImageDraw.Draw(img)
        font_size = 18  # A default font size
        font = ImageFont.truetype(font_path, font_size)

        # --- 3. Iterate over each detected text block ---
        for i in range(n_boxes):
            # We only care about actual words
            if int(ocr_data['conf'][i]) > 40: # Confidence threshold
                text = ocr_data['text'][i].strip()
                if not text:
                    continue

                # --- 4. Get coordinates and dimensions of the text box ---
                (x, y, w, h) = (ocr_data['left'][i], ocr_data['top'][i], ocr_data['width'][i], ocr_data['height'][i])

                # --- 5. Translate the text ---
                print(f"    -> Translating '{text}'...")
                try:
                    # Using 'google' translator. You can try others like 'bing', 'deepl'.
                    translated_text = ts.translate_text(text, translator='google', to_language='en')
                except Exception as e:
                    print(f"      - Could not translate text: {e}")
                    translated_text = "[Translation Error]"

                # --- 6. Cover the original text ---
                # We draw a white rectangle over the original Japanese text.
                draw.rectangle([x, y, x + w, y + h], fill='white', outline='black')

                # --- 7. Draw the translated text ---
                # Simple implementation: just draw on top.
                draw.text((x + 2, y + 2), translated_text, font=font, fill='black')

        # --- 8. Save the final image ---
        img.save(dest_path)
        print(f"    -> Saved translated image to {dest_path}")

    except FileNotFoundError:
        print(f"Error: Font file not found at {font_path}. Please check the path.")
    except Exception as e:
        print(f"An unexpected error occurred while processing {os.path.basename(image_path)}: {e}")


def main():
    """
    Main function to run the manga translation script.
    """
    print("--- Local Manga Translator ---")
    print("This script will translate manga images from a source directory.")
    print("Please make sure you have installed Tesseract-OCR and the required Python libraries.\n")

    # --- Get User Inputs ---
    source_dir = get_clean_directory_path("Enter the source directory with your manga images: ")
    dest_dir = get_clean_directory_path("Enter the destination directory for translated images: ")
    font_file = get_font_path("Enter the full path to the font file (e.g., C:\\Windows\\Fonts\\arial.ttf): ")

    print("\nStarting translation process...")
    print("-" * 30)

    # --- Process each image in the source directory ---
    supported_formats = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff')
    for filename in os.listdir(source_dir):
        if filename.lower().endswith(supported_formats):
            print(f"Processing '{filename}'...")
            source_image_path = os.path.join(source_dir, filename)
            dest_image_path = os.path.join(dest_dir, filename)
            translate_and_draw(source_image_path, dest_image_path, font_file, lang='jpn')

    print("-" * 30)
    print("Translation process completed!")
    print(f"Translated images have been saved in: {dest_dir}")


if __name__ == "__main__":
    main()