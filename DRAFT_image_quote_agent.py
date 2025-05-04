import os
import requests
from uagents import Agent, Context, Protocol
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

# --- CONFIGURATION ---
HINDI_FONT_URL = "https://github.com/googlefonts/noto-fonts/blob/main/hinted/ttf/NotoSansDevanagari/NotoSansDevanagari-Regular.ttf?raw=true"
ARABIC_FONT_URL = "https://github.com/googlefonts/noto-fonts/blob/main/hinted/ttf/NotoSansArabic/NotoSansArabic-Regular.ttf?raw=true"
HINDI_FONT_PATH = "NotoSansDevanagari-Regular.ttf"
ARABIC_FONT_PATH = "NotoSansArabic-Regular.ttf"

# --- UTILS ---
def download_font(url, path):
    if not os.path.exists(path):
        print(f"Downloading font: {path}")
        r = requests.get(url)
        with open(path, "wb") as f:
            f.write(r.content)

def generate_image_from_prompt(prompt, output_path="pollinations_image.png"):
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
    if is_arabic:
        text = get_display(arabic_reshaper.reshape(text))
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = (image.width - w) // 2
    y = (image.height - h) // 2  # Center vertically
    draw.text((x, y), text, font=font, fill=color)
    image.save(output_path)
    print(f"Image with text saved as {output_path}")

# --- AGENT SETUP ---
AGENT_SEED = os.getenv("AGENT_SEED", "image-quote-agent-seed")
AGENT_PORT = int(os.getenv("AGENT_PORT", "8100"))
AGENT_ENDPOINT = f"http://0.0.0.0:{AGENT_PORT}/submit"

image_quote_agent = Agent(
    name="image-quote-agent",
    seed=AGENT_SEED,
    port=AGENT_PORT,
    endpoint=AGENT_ENDPOINT,
    mailbox=True,
)

# --- LLM TRANSLATION (ASI1 Mini LLM API) ---
def translate_quote_with_llm(quote, target_language):
    import os, requests
    api_key = os.getenv("ASI1_LLM_API_KEY")
    if not api_key:
        raise Exception("ASI1_LLM_API_KEY not set in environment.")
    # According to https://docs.asi1.ai/docs, translation is done via the /v1/translate endpoint
    url = "https://api.asi1.ai/v1/translate"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "text": quote,
        "target_language": target_language
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        result = response.json()
        # The API returns { "translated_text": ... }
        if "translated_text" in result:
            return result["translated_text"]
        elif "result" in result:  # fallback for some LLM APIs
            return result["result"]
        else:
            raise Exception(f"Unexpected API response: {result}")
    else:
        raise Exception(f"ASI1 LLM API error: {response.status_code} - {response.text}")

# --- PROTOCOL ---
from pydantic import BaseModel

class ImageQuoteRequest(BaseModel):
    quote: str
    target_language: str
    image_prompt: str

class ImageQuoteResponse(BaseModel):
    image_path: str
    status: str

protocol = Protocol("ImageQuote")

@protocol.on_message(model=ImageQuoteRequest)
async def handle_image_quote_request(ctx: Context, sender: str, msg: ImageQuoteRequest):
    # Download fonts if needed
    download_font(HINDI_FONT_URL, HINDI_FONT_PATH)
    download_font(ARABIC_FONT_URL, ARABIC_FONT_PATH)
    try:
        translated_quote = translate_quote_with_llm(msg.quote, msg.target_language)
        image_path = generate_image_from_prompt(msg.image_prompt)
        if msg.target_language.lower() == "hindi":
            overlay_text_on_image(image_path, translated_quote, "output_with_text.png", HINDI_FONT_PATH, font_size=72, color="white", is_arabic=False)
        elif msg.target_language.lower() == "arabic":
            overlay_text_on_image(image_path, translated_quote, "output_with_text.png", ARABIC_FONT_PATH, font_size=72, color="white", is_arabic=True)
        else:
            overlay_text_on_image(image_path, translated_quote, "output_with_text.png", HINDI_FONT_PATH, font_size=72, color="white", is_arabic=False)
        ctx.send(sender, ImageQuoteResponse(image_path="output_with_text.png", status="success"))
    except Exception as e:
        ctx.send(sender, ImageQuoteResponse(image_path="", status=f"error: {e}"))

image_quote_agent.include(protocol)

if __name__ == "__main__":
    image_quote_agent.run()
    print("Agent is running! Ready to accept image quote requests.")
