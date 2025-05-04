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


if __name__ == "__main__":
    # Download fonts if not present
    download_font(HINDI_FONT_URL, HINDI_FONT_PATH)
    download_font(ARABIC_FONT_URL, ARABIC_FONT_PATH)

    # 1. Generate base image
    prompt = "Aston martin valkerie"
    base_img_path = generate_image_from_prompt(prompt, output_path="pollinations_demo_image.png")

    # 2. Overlay Hindi text
    hindi_text = "जियो, हँसो, प्यार करो"  # "Live, Laugh, Love" in Hindi
    overlay_text_on_image(base_img_path, hindi_text, "with_hindi_text.png", HINDI_FONT_PATH, font_size=72, color="white", is_arabic=False)

    # 3. Overlay Arabic text
    arabic_text = "عِشْ، اِضحَك، أَحِبّ"  # "Live, Laugh, Love" in Arabic
    overlay_text_on_image(base_img_path, arabic_text, "with_arabic_text.png", ARABIC_FONT_PATH, font_size=72, color="white", is_arabic=True)
