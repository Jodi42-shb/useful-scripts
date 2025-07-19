import os
import argparse
from PIL import Image, ImageDraw, ImageFont
import io
import textwrap

# --- Real OCR and Translation Service Integration ---
# You need to install the required libraries first:
# pip install manga-ocr translators Pillow

try:
    from manga_ocr import MangaOcr
    import translators as ts
except ImportError:
    print("Error: Required libraries not found.")
    print("Please install them by running: pip install manga-ocr translators Pillow")
    exit()

# Initialize the OCR and Translation tools
# This is done once to load the models into memory.
print("Initializing OCR and Translation models... (This may take a moment)")
mocr = MangaOcr()
print("Models initialized.")

def perform_ocr(image_bytes):
    """
    Performs OCR on the given image bytes using manga-ocr.

    Args:
        image_bytes (bytes): The byte data of the image.

    Returns:
        list: A list of dictionaries, where each dictionary contains the
              bounding box ('box') and the recognized text ('text').
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        text_blocks = mocr(image)
        # manga-ocr returns a list of text blocks. We can directly use this.
        # The format is already similar to what we need.
        print(f"  - OCR found {len(text_blocks)} text block(s).")
        return text_blocks
    except Exception as e:
        print(f"  !! OCR Error: {e}")
        return []

def translate_text(text_list):
    """
    Translates a list of texts from Japanese to English.

    Args:
        text_list (list): A list of Japanese strings.

    Returns:
        list: A list of translated English strings.
    """
    if not text_list:
        return []
    
    print(f"  - Translating {len(text_list)} text block(s)...")
    try:
        # Using the 'google' translator. You can try others like 'bing', 'deepl'.
        translated_texts = [ts.translate_text(text, translator='google', from_language='ja', to_language='en') for text in text_list]
        return translated_texts
    except Exception as e:
        print(f"  !! Translation Error: {e}")
        return ["[Translation Error]" for _ in text_list]

# --- Enhanced Image Processing Logic ---

def draw_text_in_box(draw, box, text, font_path, default_font_size=100):
    """
    Draws wrapped text inside a given bounding box, automatically adjusting
    the font size to make it fit.

    Args:
        draw (ImageDraw.Draw): The drawing context.
        box (list): The bounding box [x1, y1, x2, y2].
        text (str): The text to draw.
        font_path (str): Path to the TTF font file.
        default_font_size (int): The starting font size for adjustment.
    """
    box_width = box[2] - box[0]
    box_height = box[3] - box[1]
    font_size = default_font_size

    while font_size > 5: # Minimum font size of 5
        font = ImageFont.truetype(font_path, size=font_size)
        
        # Estimate average character width to wrap text
        avg_char_width = sum(font.getbbox(c)[2] for c in 'abcdefghijklmnopqrstuvwxyz') / 26
        max_chars_per_line = max(1, int(box_width / avg_char_width))
        
        wrapped_text = textwrap.fill(text, width=max_chars_per_line)
        
        # Check if the wrapped text fits vertically
        text_bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font)
        text_height = text_bbox[3] - text_bbox[1]

        if text_height <= box_height:
            break # This font size fits
        
        font_size -= 2 # Decrease font size and try again
    
    if font_size <= 5:
        print("  - Warning: Text may overflow box, font size is at minimum.")

    # Center the text block within the box
    text_bbox = draw.multiline_textbbox((box[0], box[1]), wrapped_text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    position_x = box[0] + (box_width - text_width) / 2
    position_y = box[1] + (box_height - text_height) / 2
    
    draw.multiline_text(
        (position_x, position_y),
        wrapped_text,
        fill='black',
        font=font,
        align='center'
    )


def process_image(image_path, output_path, font_path):
    """
    Loads an image, performs OCR, translates text, and saves the modified image.
    """
    try:
        print(f"\nProcessing image: {os.path.basename(image_path)}")

        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        
        image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")

        # 1. Perform OCR
        ocr_results = perform_ocr(image_bytes)
        if not ocr_results:
            print("  - No text found. Copying original image.")
            image.convert("RGB").save(output_path)
            return

        # 2. Translate Text
        original_texts = [result['text'] for result in ocr_results]
        translated_texts = translate_text(original_texts)

        # 3. Draw on the image
        draw = ImageDraw.Draw(image)
        for i, result in enumerate(ocr_results):
            box = result['box']
            translated_text = translated_texts[i]

            # Erase the original text by drawing a white rectangle
            draw.rectangle(box, fill='white', outline='white')
            
            # Draw the new, auto-sized, wrapped text
            draw_text_in_box(draw, box, translated_text, font_path)

        # 4. Save the final image
        # Convert to RGB before saving to avoid issues with formats like JPEG
        image.convert("RGB").save(output_path)
        print(f"  -> Saved translated image to: {os.path.basename(output_path)}")

    except Exception as e:
        print(f"  !! Error processing {os.path.basename(image_path)}: {e}")


def main(source_dir, dest_dir, font_path):
    """
    Main function to orchestrate the translation process.
    """
    print("--- Manga Translator Script Started ---")
    
    if not os.path.exists(source_dir):
        print(f"Error: Source directory not found at '{source_dir}'")
        return
        
    if not os.path.exists(font_path):
        print(f"Error: Font file not found at '{font_path}'.")
        print("Please provide a valid path to a .ttf font file.")
        return

    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    supported_formats = ('.png', '.jpg', '.jpeg', '.bmp', '.webp')

    for filename in sorted(os.listdir(source_dir)):
        if filename.lower().endswith(supported_formats):
            source_path = os.path.join(source_dir, filename)
            dest_path = os.path.join(dest_dir, filename)
            process_image(source_path, dest_path, font_path)

    print("\n--- Script Finished ---")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Translate text in manga images using real OCR and Translation APIs.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('source_dir', type=str, help='The directory containing the original manga images.')
    parser.add_argument('dest_dir', type=str, help='The directory where translated images will be saved.')
    parser.add_argument(
        '--font', 
        type=str, 
        default='arial.ttf', 
        help="Path to the .ttf font file to use for rendering text.\n"
             "Default: 'arial.ttf'. You may need to provide a full path."
    )

    args = parser.parse_args()
    
    # How to run from your terminal:
    # 1. Make sure you have the required libraries:
    #    pip install manga-ocr translators Pillow
    #
    # 2. Run the script:
    #    python your_script_name.py ./path/to/manga ./path/to/output --font /path/to/your/font.ttf
    #
    # Example:
    #    python manga_translator.py ./my_manga ./translated_manga --font C:/Windows/Fonts/arial.ttf
    
    main(args.source_dir, args.dest_dir, args.font)
