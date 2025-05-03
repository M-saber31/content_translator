import os
import pytesseract
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
import uuid
from googletrans import Translator
from models import Language, ImageContent, TranslatedContent
from datetime import datetime
from simple_lama_inpainting import SimpleLama

# Set TESSDATA_PREFIX and Tesseract command
os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR\tessdata"
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Map Language enum to Tesseract language codes
TESSERACT_LANGUAGE_MAP = {
    Language.ENGLISH: "eng",
    Language.SPANISH: "spa",
    Language.FRENCH: "fra",
    Language.GERMAN: "deu",
    Language.CHINESE: "chi_sim",
    Language.JAPANESE: "jpn",
}

class ImageProcessor:
    def __init__(self):
        self.translator = Translator()
        try:
            import torch
            self.simple_lama = SimpleLama(device="cpu")  # Force CPU usage
            print("SimpleLaMa initialized successfully on CPU")
            print("SimpleLaMa initialized successfully on CPU with PyTorch version:", torch.__version__)
        except Exception as e:
            print(f"Failed to initialize SimpleLaMa: {e}")
            self.simple_lama = None

    def extract_text(self, image_path: str, source_language: Language) -> ImageContent:
        try:
            image = Image.open(image_path)
            tesseract_lang = TESSERACT_LANGUAGE_MAP.get(source_language, source_language.value)
            text = pytesseract.image_to_string(image, lang=tesseract_lang)
            image_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()
            return ImageContent.create(image_id, image_path, source_language, extracted_text=text, timestamp=timestamp)
        except Exception as e:
            raise Exception(f"Error extracting text: {e}")

    def translate_text(self, text: str, source_language: Language, target_language: Language) -> str:
        try:
            if not text.strip():
                return ""
            translation = self.translator.translate(text, src=source_language.value, dest=target_language.value)
            return translation.text
        except Exception as e:
            raise Exception(f"Error translating text to {target_language.value}: {e}")

    def replace_text_in_image(self, original_image_path: str, original_text: str, 
                             translated_text: str, font_style: dict) -> str:
        try:
            # Load the image using PIL and convert to RGB
            image_pil = Image.open(original_image_path).convert('RGB')
            image_rgb = np.array(image_pil)  # Convert to NumPy array for Tesseract and OpenCV

            # Use Tesseract to detect text bounding boxes
            custom_config = r'--oem 3 --psm 6'
            details = pytesseract.image_to_data(image_rgb, output_type=pytesseract.Output.DICT)

            # Create a blank mask (same size as image, single channel)
            mask = np.zeros((image_rgb.shape[0], image_rgb.shape[1]), dtype=np.uint8)

            # Iterate through detected text and draw bounding boxes on the mask
            for i in range(len(details['text'])):
                if int(float(details['conf'][i])) > 20:  # Only consider confident detections
                    x, y, w, h = (
                        details['left'][i],
                        details['top'][i],
                        details['width'][i],
                        details['height'][i]
                    )
                    # Draw a filled rectangle on the mask (white = 255 for inpainting)
                    cv2.rectangle(mask, (x, y), (x + w, y + h), 255, -1)

            # Save the mask for inpainting
            mask_pil = Image.fromarray(mask)
            mask_pil.save('mask.png')

            # Perform inpainting using SimpleLaMa if available
            if self.simple_lama is not None:
                mask_pil = Image.open('mask.png').convert('L')  # Ensure mask is single-channel
                inpainted_image = self.simple_lama(image_pil, mask_pil)
                print("Inpainting completed successfully")
            else:
                inpainted_image = image_pil  # Fallback to original image if inpainting fails

            # Overlay the translated text on the inpainted image
            draw = ImageDraw.Draw(inpainted_image)
            font_path = font_style.get("family", "arial.ttf")
            font = ImageFont.truetype(font_path, int(font_style.get("size", 24)))
            color = font_style.get("color", "#000000")

            # Find a position for the translated text (using the first detected text's position if available)
            text_position = (50, 50)  # Default position
            for i in range(len(details['text'])):
                if int(float(details['conf'][i])) > 0:
                    text_position = (details['left'][i], details['top'][i])
                    break

            # Draw the translated text
            draw.text(text_position, translated_text, font=font, fill=color)

            # Save the final image
            output_path = f"edited_{uuid.uuid4()}.png"
            inpainted_image.save(output_path)
            return output_path

        except Exception as e:
            raise Exception(f"Error replacing text: {e}")