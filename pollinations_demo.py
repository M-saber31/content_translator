import requests
from PIL import Image, ImageDraw, ImageFont
import os
import arabic_reshaper
from bidi.algorithm import get_display

# URLs for Noto fonts (Google Noto fonts)
HINDI_FONT_URL = "https://github.com/googlefonts/noto-fonts/blob/main/hinted/ttf/NotoSansDevanagari/NotoSansDevanagari-Regular.ttf?raw=true"
ARABIC_FONT_URL = "https://github.com/googlefonts/noto-fonts/blob/main/hinted/ttf/NotoSansArabic/NotoSansArabic-Regular.ttf?raw=true"
HINDI_FONT_PATH = "NotoSansDevanagari-Regular.ttf"
ARABIC_FONT_PATH = "NotoSansArabic-Regular.ttf"


def download_font(url, path):
    if not os.path.exists(path):
        print(f"Downloading font: {path}")
        r = requests.get(url)
        with open(path, "wb") as f:
            f.write(r.content)


def generate_image_from_prompt(prompt, output_path="pollinations_demo_image.png"):
    url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}"
    response = requests.get(url)
    if response.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(response.content)
        print(f"Image generated and saved as {output_path}")
        return output_path
    else:
        raise Exception(f"Pollinations API error: {response.status_code}")


def overlay_text_on_image(image_path, text, output_path, font_path, font_size=64, color="white", is_arabic=False):
    image = Image.open(image_path).convert("RGBA")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_path, font_size)

    # Prepare Arabic text if needed
    if is_arabic:
        text = get_display(arabic_reshaper.reshape(text))

    # Use textbbox for accurate text size
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = (image.width - w) // 2
    y = (image.height - h) // 2  # Center vertically
    draw.text((x, y), text, font=font, fill=color)
    image.save(output_path)
    print(f"Image with text saved as {output_path}")


import pytesseract
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration
import torch

import warnings
import numpy as np
import cv2

def extract_text_from_image(image_path, lang='eng'):
    """Extract text from an image using pytesseract (no pre-processing, no custom config)."""
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang=lang)
        return text.strip()
    except Exception as e:
        print(f"OCR error: {e}")
        return None

def describe_image_background(image_path, model_name="Salesforce/blip-image-captioning-large"):
    """Describe the background of an image: if truly solid color, return color; else use BLIP captioning."""
    try:
        from collections import Counter
        import numpy as np
        img = Image.open(image_path).convert('RGB')
        img_small = img.resize((50, 50))
        pixels = list(img_small.getdata())
        arr = np.array(pixels)
        variance = arr.var(axis=0).mean()
        color_counts = Counter(pixels)
        most_common_color, most_common_count = color_counts.most_common(1)[0]
        percent_dominant = most_common_count / len(pixels)
        # Only treat as solid color if variance < 40 and dominant color covers >90%
        if variance < 40 and percent_dominant > 0.9:
            def rgb_to_name(rgb):
                r, g, b = rgb
                if r > 200 and g < 100 and b < 100:
                    return 'red'
                elif r < 100 and g > 200 and b < 100:
                    return 'green'
                elif r < 100 and g < 100 and b > 200:
                    return 'blue'
                elif r > 200 and g > 200 and b < 100:
                    return 'yellow'
                elif r > 200 and g > 200 and b > 200:
                    return 'white'
                elif r < 50 and g < 50 and b < 50:
                    return 'black'
                elif r > 200 and g < 100 and b > 200:
                    return 'magenta'
                elif r < 100 and g > 200 and b > 200:
                    return 'cyan'
                else:
                    return f'rgb{rgb}'
            color_name = rgb_to_name(most_common_color)
            return f"{color_name} background"
        # Else, use BLIP
        warnings.filterwarnings("ignore")
        processor = BlipProcessor.from_pretrained(model_name)
        model = BlipForConditionalGeneration.from_pretrained(model_name)
        inputs = processor(img, return_tensors="pt")
        with torch.no_grad():
            out = model.generate(**inputs, max_new_tokens=50, num_beams=5)
        caption = processor.decode(out[0], skip_special_tokens=True)
        return caption
    except Exception as e:
        print(f"Background description error: {e}")
        return None

if __name__ == "__main__":
    # Download fonts if not present
    download_font(HINDI_FONT_URL, HINDI_FONT_PATH)
    download_font(ARABIC_FONT_URL, ARABIC_FONT_PATH)

    # Prompt user for image path
    user_image_path = input("Enter the path to your image file: ").strip()
    import os
    if not os.path.exists(user_image_path):
        print(f"Image file '{user_image_path}' does not exist. Exiting.")
        exit(1)

    # 1. Extract text from user image
    extracted_text = extract_text_from_image(user_image_path)
    if extracted_text:
        print(f"Extracted Text: {extracted_text}")
    else:
        print("Extracted Text: [No text detected]")
        extracted_text = ""  # fallback

    # 2. Get background description from user image
    background_desc = describe_image_background(user_image_path)
    if background_desc:
        print(f"Background Description: {background_desc}")
    else:
        print("Background Description: [No description generated]")
        background_desc = "A beautiful landscape"  # fallback

    # 3. Generate new image using background description as prompt
    gen_img_path = generate_image_from_prompt(background_desc, output_path="pollinations_demo_image.png")

    # 4. Translate the extracted text using asi1 API
    import requests
    import os
    from dotenv import load_dotenv
    load_dotenv()
    asi1_api_key = os.getenv("ASI1_API_KEY")
    if not asi1_api_key:
        raise RuntimeError("ASI1_API_KEY not found in environment. Please add it to your .env file.")
    def translate_text_asi1(text, target_lang):
        import json
        url = "https://api.asi1.ai/v1/chat/completions"
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {asi1_api_key}'
        }
        lang_name = {"hi": "Hindi", "ar": "Arabic"}.get(target_lang, target_lang)
        prompt = f"Translate the following text to {lang_name}: {text}. Only output the translated text."
        payload = json.dumps({
            "model": "asi1-mini",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0,
            "stream": False,
            "max_tokens": 0
        })
        try:
            resp = requests.post(url, headers=headers, data=payload)
            if resp.status_code == 200:
                result = resp.json()
                translation = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                if translation:
                    print(f"Translation ({target_lang}): {translation}")
                    return translation
                else:
                    print(f"Translation ({target_lang}) empty, falling back to English.")
                    return text
            else:
                print(f"Translation error ({target_lang}): {resp.text}")
                return text
        except Exception as e:
            print(f"Translation exception ({target_lang}): {e}")
            return text
    
    text_en = extracted_text
    # Preprocess for Hindi and Arabic overlays
    text_hi_input = extracted_text.replace('|', '।')
    text_ar_input = extracted_text.replace('|', '،')
    text_hi = translate_text_asi1(text_hi_input, "hi")
    text_ar = translate_text_asi1(text_ar_input, "ar")
    
    # 5. Overlay English text
    ARIAL_REGULAR_PATH = r"C:\\Windows\\Fonts\\arial.ttf"
    DEJAVU_PATH = "DejaVuSans.ttf"
    if os.path.exists(ARIAL_REGULAR_PATH):
        font_path_en = ARIAL_REGULAR_PATH
        print("Using Arial Regular for English overlay.")
    else:
        if not os.path.exists(DEJAVU_PATH):
            url = "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans.ttf"
            r = requests.get(url)
            with open(DEJAVU_PATH, "wb") as f:
                f.write(r.content)
        font_path_en = DEJAVU_PATH
        print("Warning: Arial Regular not found, using DejaVuSans for English overlay.")
    overlay_text_on_image(
        gen_img_path,
        text_en,
        "output_with_text_overlay_en.png",
        font_path_en,
        font_size=72,
        color="white",
        is_arabic=False
    )
    # 6. Overlay Hindi text
    overlay_text_on_image(
        gen_img_path,
        text_hi,
        "output_with_text_overlay_hi.png",
        HINDI_FONT_PATH,  # Ensure this is a Hindi-capable font
        font_size=72,
        color="white",
        is_arabic=False
    )
    # 7. Overlay Arabic text
    overlay_text_on_image(
        gen_img_path,
        text_ar,
        "output_with_text_overlay_ar.png",
        ARABIC_FONT_PATH,  # Ensure this is an Arabic-capable font
        font_size=72,
        color="white",
        is_arabic=True
    )
    print("Image generation and overlay complete. See output_with_text_overlay_en.png, output_with_text_overlay_hi.png, output_with_text_overlay_ar.png.")


