import os
import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageDraw, ImageFont
import textwrap
from deep_translator import GoogleTranslator

# Configuration
FONT_SIZE = 20
OCR_LANG = 'jpn'  # Japanese language for OCR

def preprocess_for_ocr(image):
    """Preprocess the image for better OCR accuracy."""
    if len(image.shape) == 2:  # Grayscale image
        gray = image
    elif image.shape[2] == 4:  # RGBA
        gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
    else:  # RGB
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Apply adaptive thresholding to enhance text
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    return binary

def perform_ocr(image_path):
    """Perform OCR using pytesseract and return text with bounding boxes."""
    image = cv2.imread(image_path)
    if image is None:
        print(f"  - Could not read image: {image_path}")
        return []
    preprocessed_image = preprocess_for_ocr(image)
    # Get detailed OCR data
    data = pytesseract.image_to_data(
        preprocessed_image, lang=OCR_LANG, output_type=pytesseract.Output.DICT
    )
    text_blocks = []
    for i in range(len(data['text'])):
        confidence = int(data['conf'][i])
        if confidence > 40:  # Filter low-confidence results
            text = data['text'][i].strip()
            if text:
                # Bounding box: [left, top, right, bottom]
                box = [
                    data['left'][i],
                    data['top'][i],
                    data['left'][i] + data['width'][i],
                    data['top'][i] + data['height'][i]
                ]
                text_blocks.append({'text': text, 'box': box})
    print(f"  - OCR found {len(text_blocks)} text block(s).")
    return text_blocks

def translate_text(text_list):
    """Translate a list of Japanese texts to English."""
    if not text_list:
        return []
    print(f"  - Translating {len(text_list)} text block(s)...")
    try:
        translated_texts = [
            GoogleTranslator(source='ja', target='en').translate(text)
            for text in text_list
        ]
        return translated_texts
    except Exception as e:
        print(f"  !! Translation Error: {e}")
        return ["[Translation Error]" for _ in text_list]

def draw_text_in_box(draw, box, text, font_path, default_font_size=100):
    """Draw translated text within the bounding box, adjusting font size."""
    box_width = box[2] - box[0]
    box_height = box[3] - box[1]
    font_size = default_font_size
    while font_size > 5:
        font = ImageFont.truetype(font_path, size=font_size)
        # Estimate characters per line based on font width
        avg_char_width = sum(font.getbbox(c)[2] for c in 'abcdefghijklmnopqrstuvwxyz') / 26
        max_chars_per_line = max(1, int(box_width / avg_char_width))
        wrapped_text = textwrap.fill(text, width=max_chars_per_line)
        text_bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font)
        text_height = text_bbox[3] - text_bbox[1]
        if text_height <= box_height:
            break
        font_size -= 2
    if font_size <= 5:
        print("  - Warning: Text may overflow box, font size at minimum.")
    # Center the text in the box
    text_bbox = draw.multiline_textbbox((box[0], box[1]), wrapped_text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    position_x = box[0] + (box_width - text_width) / 2
    position_y = box[1] + (box_height - text_height) / 2
    draw.multiline_text(
        (position_x, position_y), wrapped_text, fill='black', font=font, align='center'
    )

def process_image(image_path, output_path, font_path):
    """Process a single image: OCR, translate, and overlay text."""
    try:
        print(f"\nProcessing image: {os.path.basename(image_path)}")
        ocr_results = perform_ocr(image_path)
        if not ocr_results:
            print("  - No text found. Copying original image.")
            image = cv2.imread(image_path)
            cv2.imwrite(output_path, image)
            return
        original_texts = [result['text'] for result in ocr_results]
        translated_texts = translate_text(original_texts)
        image = Image.open(image_path).convert("RGBA")
        draw = ImageDraw.Draw(image)
        for i, result in enumerate(ocr_results):
            box = result['box']
            translated_text = translated_texts[i]
            draw.rectangle(box, fill='white', outline='white')  # Cover original text
            draw_text_in_box(draw, box, translated_text, font_path)
        image.convert("RGB").save(output_path)
        print(f"  -> Saved translated image to: {os.path.basename(output_path)}")
    except Exception as e:
        print(f"  !! Error processing {os.path.basename(image_path)}: {e}")

def main(source_dir, dest_dir, font_path):
    """Main function to process all images in the source directory."""
    print("--- Manga Translator Script Started ---")
    supported_formats = ('.png', '.jpg', '.jpeg', '.bmp', '.webp')
    for filename in sorted(os.listdir(source_dir)):
        if filename.lower().endswith(supported_formats):
            source_path = os.path.join(source_dir, filename)
            dest_path = os.path.join(dest_dir, filename)
            process_image(source_path, dest_path, font_path)
    print("\n--- Script Finished ---")

if __name__ == '__main__':
    print("Welcome to the Manga Translator Script!")
    source_dir = input("Please enter the path to the directory containing your manga images: ").strip()
    while not os.path.exists(source_dir):
        print("Source directory does not exist. Please enter a valid path.")
        source_dir = input("Please enter the path to the directory containing your manga images: ").strip()
    font_path = input("Please enter the path to the .ttf font file: ").strip()
    while not os.path.exists(font_path):
        print("Font file does not exist. Please enter a valid path.")
        font_path = input("Please enter the path to the .ttf font file: ").strip()
    dest_dir = input("Please enter the path for the directory where translated images will be saved: ").strip()
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
        print(f"Created destination directory: {dest_dir}")
    main(source_dir, dest_dir, font_path)