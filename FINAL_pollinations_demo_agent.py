"""
FINAL Pollinations Demo Agent

This agent wraps the functionality of pollinations_demo.py as a callable agent using the uAgents framework.
"""

import os
from uagents import Agent, Context, Model
from dotenv import load_dotenv

# Import the main logic from pollinations_demo.py
import sys
sys.path.append(os.path.dirname(__file__))
from pollinations_demo import extract_text_from_image, describe_image_background, generate_image_from_prompt, overlay_text_on_image, HINDI_FONT_PATH, ARABIC_FONT_PATH, download_font

# Load environment variables
load_dotenv()

class ImageGenRequest(Model):
    image_path: str

class ImageGenResponse(Model):
    extracted_text: str
    background_desc: str
    output_files: list

agent = Agent(
    name="pollinations_demo_agent",
    seed=os.getenv("AGENT_SEED", "pollinationsdemoagent", mailbox=True),
)

@agent.on_message(model=ImageGenRequest, replies=ImageGenResponse)
async def handle_image_request(ctx: Context, msg: ImageGenRequest):
    # Download fonts if not present
    download_font(os.getenv("HINDI_FONT_URL"), HINDI_FONT_PATH)
    download_font(os.getenv("ARABIC_FONT_URL"), ARABIC_FONT_PATH)

    user_image_path = msg.image_path
    if not os.path.exists(user_image_path):
        ctx.logger.error(f"Image file '{user_image_path}' does not exist.")
        await ctx.send(ImageGenResponse(
            extracted_text="",
            background_desc="",
            output_files=[],
        ))
        return

    extracted_text = extract_text_from_image(user_image_path)
    if not extracted_text:
        extracted_text = ""
    background_desc = describe_image_background(user_image_path)
    if not background_desc:
        background_desc = "A beautiful landscape"

    # Generate new image
    gen_img_path = generate_image_from_prompt(background_desc, output_path="pollinations_demo_image.png")

    # Translation logic (same as in pollinations_demo.py)
    import requests
    import json
    asi1_api_key = os.getenv("ASI1_API_KEY")
    def translate_text_asi1(text, target_lang):
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
                    return translation
                else:
                    return text
            else:
                return text
        except Exception:
            return text

    text_en = extracted_text
    text_hi_input = extracted_text.replace('|', '।')
    text_ar_input = extracted_text.replace('|', '،')
    text_hi = translate_text_asi1(text_hi_input, "hi")
    text_ar = translate_text_asi1(text_ar_input, "ar")

    # Overlay
    ARIAL_REGULAR_PATH = r"C:\\Windows\\Fonts\\arial.ttf"
    DEJAVU_PATH = "DejaVuSans.ttf"
    if os.path.exists(ARIAL_REGULAR_PATH):
        font_path_en = ARIAL_REGULAR_PATH
    else:
        font_path_en = DEJAVU_PATH
    output_files = []
    overlay_text_on_image(
        gen_img_path,
        text_en,
        "output_with_text_overlay_en.png",
        font_path_en,
        font_size=72,
        color="white",
        is_arabic=False
    )
    output_files.append("output_with_text_overlay_en.png")
    overlay_text_on_image(
        gen_img_path,
        text_hi,
        "output_with_text_overlay_hi.png",
        HINDI_FONT_PATH,
        font_size=72,
        color="white",
        is_arabic=False
    )
    output_files.append("output_with_text_overlay_hi.png")
    overlay_text_on_image(
        gen_img_path,
        text_ar,
        "output_with_text_overlay_ar.png",
        ARABIC_FONT_PATH,
        font_size=72,
        color="white",
        is_arabic=True
    )
    output_files.append("output_with_text_overlay_ar.png")
    await ctx.send(ImageGenResponse(
        extracted_text=extracted_text,
        background_desc=background_desc,
        output_files=output_files,
    ))

if __name__ == "__main__":
    agent.run()
