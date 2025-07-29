import os
import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageDraw, ImageFont
from deep_translator import GoogleTranslator
import glob
from collections import defaultdict
import traceback
import time
import math

# ------------------------------------------------------------------------------
# --- SETUP & CONFIGURATION ---
# ------------------------------------------------------------------------------
#
# --- ⚠️ IMPORTANT SETUP ⚠️ ---
# 1. Run the `setup_manga_translator.py` script first.
#
# 2. If you installed Tesseract to a custom location and did not add it to your
#    system's PATH, you may need to specify its location below.
#    (On Windows, you might need to uncomment and edit the following line)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
#
# ------------------------------------------------------------------------------

# --- FONT SETTINGS ---
# The setup script downloads this font automatically.
FONT_FILE = 'mangat.ttf'
FONT_SIZE = 22

# --- OCR & TRANSLATION SETTINGS ---
# Confidence threshold for detected text (0-100). Higher values are stricter.
OCR_CONFIDENCE = 40
# Languages for Tesseract to detect. 'jpn+jpn_vert' handles both horizontal and vertical text.
OCR_LANG = 'jpn+jpn_vert'
# Number of times to retry a failed translation
TRANSLATION_RETRIES = 3


def preprocess_for_ocr(image):
    """Converts image to a format that is easier for Tesseract to read."""
    # If the image is already grayscale, no conversion is needed.
    if len(image.shape) == 2:
        gray = image
    # If the image has 4 channels (e.g., PNG with alpha), convert to BGR first.
    elif image.shape[2] == 4:
        gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
    # If the image has 3 channels (standard BGR), convert to grayscale.
    else:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply adaptive thresholding to binarize the image. This helps with varied lighting.
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 11, 2)
    return binary


def group_text_blocks(data, max_distance_multiplier=1.5):
    """
    Groups words into text blocks based on their proximity.
    This is much more reliable for manga than Tesseract's block/line numbers.
    """
    words = []
    for i in range(len(data['text'])):
        conf = int(float(data['conf'][i]))
        text = data['text'][i].strip()
        if conf > OCR_CONFIDENCE and text:
            word = {
                'text': text,
                'left': data['left'][i],
                'top': data['top'][i],
                'width': data['width'][i],
                'height': data['height'][i],
                'center_x': data['left'][i] + data['width'][i] / 2,
                'center_y': data['top'][i] + data['height'][i] / 2,
                'visited': False
            }
            words.append(word)

    if not words:
        return []

    avg_height = sum(w['height'] for w in words) / len(words)
    max_dist = avg_height * max_distance_multiplier

    blocks = []
    for i, word in enumerate(words):
        if word['visited']:
            continue
        
        current_block = []
        queue = [word]
        word['visited'] = True
        
        while queue:
            current_word = queue.pop(0)
            current_block.append(current_word)
            
            for other_word in words:
                if other_word['visited']:
                    continue
                
                dist = math.hypot(current_word['center_x'] - other_word['center_x'],
                                  current_word['center_y'] - other_word['center_y'])
                
                if dist < max_dist:
                    other_word['visited'] = True
                    queue.append(other_word)
        
        blocks.append(current_block)
        
    return blocks


def wrap_text(text, font, max_width):
    """Wraps text to fit into a bounding box."""
    lines = []
    if not text or max_width <= 0:
        return lines

    words = text.split()
    while words:
        line = ''
        while words and font.getbbox(line + words[0])[2] <= max_width:
            line += words.pop(0) + ' '
        
        if not line and words:
            line = words.pop(0) + ' '
            
        lines.append(line.strip())
    return [line for line in lines if line]


def draw_text_with_outline(draw, position, text, font, fill_color, outline_color):
    """Draws text with an outline for better readability."""
    x, y = position
    for dx, dy in [(-1,-1), (-1,1), (1,-1), (1,1), (-2,0), (2,0), (0,-2), (0,2)]:
        draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
    draw.text(position, text, font=font, fill=fill_color)


def process_image(image_path, output_path, font_path, font_size):
    """Processes a single manga image for translation."""
    try:
        with open(image_path, 'rb') as f:
            stream = f.read()
        numpyarray = np.frombuffer(stream, np.uint8)
        original_image = cv2.imdecode(numpyarray, cv2.IMREAD_UNCHANGED)

        if original_image is None:
            print(f"  - ⚠️ Could not read image: {image_path}")
            return

        print("  - 🔍 Pre-processing image for OCR...")
        preprocessed_image = preprocess_for_ocr(original_image)

        print(f"  - 📖 Detecting text with Tesseract (lang={OCR_LANG})...")
        tessdata_dir = os.path.abspath('tessdata')
        os.environ['TESSDATA_PREFIX'] = tessdata_dir
        # --- FIX: Use Page Segmentation Mode 11 for sparse text ---
        tess_config = f'--psm 11'
        data = pytesseract.image_to_data(preprocessed_image, lang=OCR_LANG, config=tess_config, output_type=pytesseract.Output.DICT)

        # --- FIX: Use new proximity-based grouping ---
        text_blocks = group_text_blocks(data)

        if not text_blocks:
            print("  - 🤷 No translatable text found. Saving original image.")
            is_success, im_buf_arr = cv2.imencode(".png", original_image)
            im_buf_arr.tofile(output_path)
            return

        translations_to_draw = []
        inpainting_mask = np.zeros(original_image.shape[:2], dtype=np.uint8)

        print(f"  - 🌐 Found {len(text_blocks)} text blocks. Translating...")
        for block in text_blocks:
            # Reconstruct the full text from the block
            # Sort by horizontal position for left-to-right, or vertical for top-to-bottom
            block.sort(key=lambda w: (w['top'], w['left']))
            full_text = "".join([w['text'] for w in block]).strip()
            if not full_text:
                continue

            # Calculate the encompassing bounding box for the entire block
            x1 = min(w['left'] for w in block)
            y1 = min(w['top'] for w in block)
            x2 = max(w['left'] + w['width'] for w in block)
            y2 = max(w['top'] + w['height'] for w in block)
            box_w, box_h = x2 - x1, y2 - y1

            cv2.rectangle(inpainting_mask, (x1 - 5, y1 - 5), (x2 + 5, y2 + 5), 255, -1)

            translated_text = None
            print(f"    - Original: '{full_text}'")
            for attempt in range(TRANSLATION_RETRIES):
                try:
                    translated_text = GoogleTranslator(source='ja', target='en').translate(full_text, timeout=10)
                    if translated_text:
                        break 
                except Exception as e:
                    print(f"    - ⚠️ Translation attempt {attempt + 1}/{TRANSLATION_RETRIES} failed: {e}")
                    if attempt < TRANSLATION_RETRIES - 1:
                        time.sleep(1)
            
            print(f"    - Translated: '{translated_text}'")
            
            if translated_text and translated_text.strip() and translated_text.strip().lower() != full_text.strip().lower():
                print(f"    - ✅ Translation successful.")
                translations_to_draw.append({'text': translated_text, 'box': (x1, y1, box_w, box_h)})
            else:
                print(f"    - ❌ Translation failed or returned original text. Skipping block.")

        if not translations_to_draw:
            print("  - 🤷 Text was detected, but no valid translations were generated. Skipping.")
            is_success, im_buf_arr = cv2.imencode(".png", original_image)
            im_buf_arr.tofile(output_path)
            return

        print("  - 🖌️ Erasing original text...")
        inpainted_image = cv2.inpaint(original_image, inpainting_mask, inpaintRadius=5, flags=cv2.INPAINT_TELEA)

        print("  - ✍️ Drawing translated text...")
        if len(inpainted_image.shape) == 2:
             pil_ready_image = cv2.cvtColor(inpainted_image, cv2.COLOR_GRAY2RGB)
        elif inpainted_image.shape[2] == 4:
             pil_ready_image = cv2.cvtColor(inpainted_image, cv2.COLOR_BGRA2RGB)
        else:
             pil_ready_image = cv2.cvtColor(inpainted_image, cv2.COLOR_BGR2RGB)

        pil_image = Image.fromarray(pil_ready_image)
        draw = ImageDraw.Draw(pil_image)
        
        try:
            font = ImageFont.truetype(font_path, font_size)
        except IOError:
            print(f"  - ❌ FONT ERROR: Could not load font {font_path}. Using default font.")
            font = ImageFont.load_default()

        for item in translations_to_draw:
            box, text = item['box'], item['text']
            box_x, box_y, box_w, box_h = box

            wrapped_lines = wrap_text(text, font, box_w)
            if not wrapped_lines:
                continue
            
            line_heights = [font.getbbox(line)[3] - font.getbbox(line)[1] + 5 for line in wrapped_lines]
            total_text_height = sum(line_heights)

            y_text = box_y + (box_h - total_text_height) / 2
            
            for i, line in enumerate(wrapped_lines):
                line_width = font.getbbox(line)[2]
                x_text = box_x + (box_w - line_width) / 2
                
                draw_text_with_outline(draw, (x_text, y_text), line, font, (255, 255, 255), (0, 0, 0))
                y_text += line_heights[i]

        final_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        is_success, im_buf_arr = cv2.imencode(".png", final_image)
        im_buf_arr.tofile(output_path)
        print(f"  - ✅ Successfully saved to {output_path}")

    except Exception as e:
        print(f"  - ❌ An unexpected error occurred while processing {image_path}: {e}")
        traceback.print_exc()


# --- MAIN EXECUTION ---
if __name__ == "__main__":
    if not os.path.exists(FONT_FILE):
        print(f"❌ FONT ERROR: The font file '{FONT_FILE}' was not found.")
        print("Please run the `setup_manga_translator.py` script first to download it.")
        exit()
    
    tessdata_dir = os.path.abspath('tessdata')
    if not os.path.exists(tessdata_dir):
        print(f"❌ TESSERACT DATA ERROR: The 'tessdata' directory was not found.")
        print("Please run the `setup_manga_translator.py` script first to download language files.")
        exit()
    os.environ['TESSDATA_PREFIX'] = tessdata_dir

    print("--- 📖 Manga Translator Pro ---")

    source_dir = input("➡️ Enter the path to the folder containing your images: ").strip()
    if not os.path.isdir(source_dir):
        print(f"❌ ERROR: The source directory '{source_dir}' does not exist.")
        exit()

    dest_dir = input("⬅️ Enter the path for the folder where translated images will be saved: ").strip()
    if not os.path.isdir(dest_dir):
        print(f"Directory '{dest_dir}' not found. Creating it...")
        try:
            os.makedirs(dest_dir)
        except OSError as e:
            print(f"❌ ERROR: Could not create directory '{dest_dir}'. Reason: {e}")
            exit()

    supported_extensions = ['*.png', '*.jpg', '*.jpeg', '*.webp', '*.bmp', '*.tif', '*.tiff']
    image_files = []
    print("\nSearching for images...")

    safe_source_dir = glob.escape(source_dir)

    for ext in supported_extensions:
        search_pattern = os.path.join(safe_source_dir, ext)
        image_files.extend(glob.glob(search_pattern))

    if not image_files:
        print(f"No supported images found in '{source_dir}'.")
        print("Please check the folder and ensure images are directly inside, not in subfolders.")
    else:
        print(f"Found {len(image_files)} images to process.")
        image_files.sort()

        for i, image_file in enumerate(image_files):
            print(f"\n--- Processing file {i+1}/{len(image_files)}: {os.path.basename(image_file)} ---")
            base_name = os.path.splitext(os.path.basename(image_file))[0]
            output_filename = os.path.join(dest_dir, f"translated_{base_name}.png")
            process_image(image_file, output_filename, FONT_FILE, FONT_SIZE)

        print("\n🎉 All tasks completed!")