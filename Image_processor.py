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
            # Set canvas size (optionally, use the original image size)
            width, height = 800, 400  # Default size; can be adjusted or read from original image
            try:
                with Image.open(original_image_path) as img:
                    width, height = img.size
            except Exception:
                pass

            # Create a black canvas
            canvas = Image.new('RGB', (width, height), color='black')
            draw = ImageDraw.Draw(canvas)
            font_path = font_style.get("family", "arial.ttf")
            font_size = int(font_style.get("size", 48))
            color = font_style.get("color", "#FFFFFF")  # White text on black
            font = ImageFont.truetype(font_path, font_size)

            # Use the translated_text if available, otherwise original_text
            text_to_draw = translated_text if translated_text.strip() else original_text
            if not text_to_draw.strip():
                text_to_draw = "[No text found by OCR]"

            # Draw the text centered
            lines = text_to_draw.strip().split("\n")
            y_offset = 40
            for line in lines:
                w, h = draw.textsize(line, font=font)
                x = (width - w) // 2
                draw.text((x, y_offset), line, font=font, fill=color)
                y_offset += h + 10

            # Save the canvas
            output_path = f"canvas_{uuid.uuid4()}.png"
            canvas.save(output_path)
            print(f"Canvas image saved at: {output_path}")
            return output_path

        except Exception as e:
            raise Exception(f"Error creating canvas with text: {e}")