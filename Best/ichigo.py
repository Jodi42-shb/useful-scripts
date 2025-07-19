import os
import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageDraw, ImageFont
from deep_translator import GoogleTranslator
import glob
from collections import defaultdict

# --- CONFIGURATION ---
FONT_FILE = 'mangat.ttf'
FONT_SIZE = 20
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def wrap_text(text, font, max_width):
    """Wraps text to fit into a bounding box."""
    lines = []
    if not text:
        return lines

    words = text.split()
    while words:
        line = ''
        while words and font.getlength(line + words[0]) <= max_width:
            line += (words.pop(0) + ' ')
        lines.append(line.strip())
    return lines

def process_image(image_path, output_path, font_path, font_size):
    """Processes a single manga image for translation."""
    try:
        original_image = cv2.imread(image_path)
        if original_image is None:
            print(f"  - ⚠️ Could not read image: {image_path}")
            return
        
        inpainting_mask = np.zeros(original_image.shape[:2], dtype=np.uint8)
        data = pytesseract.image_to_data(original_image, lang='jpn', output_type=pytesseract.Output.DICT)
        
        num_boxes = len(data['level'])
        text_blocks = defaultdict(list)
        for i in range(num_boxes):
            if int(data['conf'][i]) > 40:
                block_num = data['block_num'][i]
                text_blocks[block_num].append(i)

        translations_to_draw = []

        for block_num in sorted(text_blocks.keys()):
            indices = text_blocks[block_num]
            block_text = " ".join([data['text'][i] for i in indices]).strip()
            if not block_text:
                continue

            x_coords, y_coords = [data['left'][i] for i in indices], [data['top'][i] for i in indices]
            w_coords, h_coords = [data['width'][i] for i in indices], [data['height'][i] for i in indices]
            x, y = min(x_coords), min(y_coords)
            w, h = max(x_coords) + max(w_coords) - x, max(y_coords) + max(h_coords) - y

            cv2.rectangle(inpainting_mask, (x - 5, y - 5), (x + w + 5, y + h + 5), 255, -1)
            
            try:
                translated_text = GoogleTranslator(source='ja', target='en').translate(block_text)
                if translated_text:
                    translations_to_draw.append({'text': translated_text, 'box': (x, y, w, h)})
            except Exception as e:
                print(f"  - 翻訳失敗 (Translation failed): {e}")
        
        if not translations_to_draw:
            print("  - 🤷 No translatable text found. Skipping.")
            cv2.imwrite(output_path, original_image)
            return

        print("  - 🖌️ Erasing original text...")
        inpainted_image = cv2.inpaint(original_image, inpainting_mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)

        print("  - ✍️ Drawing translated text...")
        pil_image = Image.fromarray(cv2.cvtColor(inpainted_image, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_image)
        font = ImageFont.truetype(font_path, font_size)

        for item in translations_to_draw:
            box, text = item['box'], item['text']
            wrapped_lines = wrap_text(text, font, box[2])
            y_text = box[1]
            for line in wrapped_lines:
                draw.text((box[0], y_text), line, font=font, fill=(0, 0, 0))
                y_text += font.getmetrics()[0] + 2

        final_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB_BGR)
        cv2.imwrite(output_path, final_image)
        print(f"  - ✅ Successfully saved to {output_path}")

    except Exception as e:
        print(f"  - ❌ An unexpected error occurred while processing {image_path}: {e}")

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    if not os.path.exists(FONT_FILE):
        print(f"❌ FONT ERROR: The font file '{FONT_FILE}' was not found in this directory.")
        exit()

    print("--- 📖 Manga Translator Pro ---")
    
    # FIX 1: Use .strip() to remove leading/trailing whitespace from user input.
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

    # FIX 2: Use glob.escape() to handle special characters like [ ] in the path.
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