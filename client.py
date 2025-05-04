import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from uagents import Agent, Context
from models import Language, Platform, TimeZone, ProcessImageRequest, ProcessImageResponse, SchedulePostRequest, SchedulePostResponse

# Load environment variables
load_dotenv()

# Client configuration
CLIENT_SEED = os.getenv("CLIENT_SEED", "content-translator-client-seed")
CLIENT_PORT = int(os.getenv("CLIENT_PORT", "8001"))
CLIENT_ENDPOINT = f"http://localhost:{CLIENT_PORT}/submit"
CONTENT_TRANSLATOR_ADDRESS = os.getenv("CONTENT_TRANSLATOR_ADDRESS", "")

# Create the client agent
client_agent = Agent(
    name="content-translator-client",
    seed=CLIENT_SEED,
    port=CLIENT_PORT,
    endpoint=CLIENT_ENDPOINT,
)

@client_agent.on_event("startup")
async def startup(ctx: Context):
    """
    Initialize the client agent on startup.
    """
    ctx.logger.info(f"Content Translator Client started with address: {client_agent.address}")
    if not CONTENT_TRANSLATOR_ADDRESS:
        ctx.logger.warning("Content translator agent address not configured.")
        return
    await process_image(ctx)

async def process_image(ctx: Context):
    """
    Send a request to process an image.
    """
    ctx.logger.info("Requesting image processing")
    try:
        await ctx.send(CONTENT_TRANSLATOR_ADDRESS, ProcessImageRequest(
            image_path="image.jpg",
            source_language=Language.ENGLISH,
            target_languages=[Language.SPANISH, Language.FRENCH],
            font_style={"family": "arial.ttf", "size": "24", "color": "#000000"}
        ))
    except Exception as e:
        ctx.logger.error(f"Error requesting image processing: {e}")

async def schedule_posts(ctx: Context, image_id: str):
    """
    Send a request to schedule posts.
    """
    ctx.logger.info("Requesting post scheduling")
    try:
        await ctx.send(CONTENT_TRANSLATOR_ADDRESS, SchedulePostRequest(
            image_id=image_id,
            platforms=[Platform.INSTAGRAM, Platform.TWITTER],
            language_time_zones={
                Language.SPANISH: TimeZone.CET,
                Language.FRENCH: TimeZone.CET
            },
            optimal_time="18:00"
        ))
    except Exception as e:
        ctx.logger.error(f"Error requesting post scheduling: {e}")

@client_agent.on_message(model=ProcessImageResponse)
async def handle_process_image_response(ctx: Context, sender: str, msg: ProcessImageResponse):
    """
    Handle the image processing response.
    """
    ctx.logger.info(f"Received image processing response from {sender}")
    if msg.original_content:
        ctx.logger.info(f"Extracted text: {msg.original_content.extracted_text}")
        for translated_content in msg.translated_contents:
            ctx.logger.info(f"Translated to {translated_content.target_language.value}: {translated_content.translated_text}")
            ctx.logger.info(f"Edited image: {translated_content.edited_image_path}")
        # Schedule posts using the actual image_id
        await schedule_posts(ctx, msg.image_id)
    else:
        ctx.logger.error("Image processing failed: No original content returned")

@client_agent.on_message(model=SchedulePostResponse)
async def handle_schedule_post_response(ctx: Context, sender: str, msg: SchedulePostResponse):
    """
    Handle the post scheduling response.
    """
    ctx.logger.info(f"Received post scheduling response from {sender}")
    if msg.schedules:
        for schedule in msg.schedules:
            ctx.logger.info(f"Scheduled post for {schedule.platform.value} in {schedule.target_language.value} at {schedule.scheduled_time}")
    else:
        ctx.logger.error("Post scheduling failed: No schedules returned")

if __name__ == "__main__":
    client_agent.run()