import os
import uuid
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from uagents import Agent, Context
from uagents.experimental.quota import QuotaProtocol, RateLimit
from models import (
    Language, Platform, TimeZone, ImageContent, TranslatedContent, PostSchedule,
    ProcessImageRequest, ProcessImageResponse, SchedulePostRequest, SchedulePostResponse
)
from Image_processor import ImageProcessor
from scheduler import PostScheduler

# Load environment variables
load_dotenv()

# Agent configuration
AGENT_SEED = os.getenv("AGENT_SEED", "content-translator-agent-seed")
AGENT_PORT = int(os.getenv("AGENT_PORT", "8000"))
AGENT_ENDPOINT = f"http://0.0.0.0:{AGENT_PORT}/submit"

# Create the agent
content_translator = Agent(
    name="content-translator",
    seed=AGENT_SEED,
    port=AGENT_PORT,
    endpoint=AGENT_ENDPOINT,
)

# Create a protocol with rate limiting
translator_protocol = QuotaProtocol(
    storage_reference=content_translator.storage,
    name="Content-Translator-Protocol",
    version="0.1.0",
    default_rate_limit=RateLimit(window_size_minutes=1, max_requests=10),
)

# Global agent instance
AGENT_INSTANCE = None

class ContentTranslatorAgent:
    def __init__(self, ctx: Context):
        try:
            self.ctx = ctx
            self.image_processor = ImageProcessor()
            self.scheduler = PostScheduler()
            self._initialize_storage()
        except Exception as e:
            ctx.logger.error(f"Failed to initialize ContentTranslatorAgent: {e}")
            raise

    def _initialize_storage(self):
        if not self.ctx.storage.get("images"):
            self.ctx.storage.set("images", {})
        if not self.ctx.storage.get("translations"):
            self.ctx.storage.set("translations", {})
        if not self.ctx.storage.get("schedules"):
            self.ctx.storage.set("schedules", [])

    async def process_image(self, request: ProcessImageRequest) -> ProcessImageResponse:
        self.ctx.logger.info(f"Processing image: {request.image_path}")
        try:
            # Extract text
            self.ctx.logger.info("Extracting text")
            image_content = self.image_processor.extract_text(
                request.image_path, request.source_language
            )
            self.ctx.logger.info(f"Extracted text: {image_content.extracted_text}")
            if not image_content.extracted_text.strip():
                self.ctx.logger.warning("No text extracted from image")
                image_content = ImageContent(image_id=image_content.image_id, image_path=request.image_path, source_language=request.source_language, extracted_text="", timestamp=datetime.now().isoformat())
            self.ctx.storage.get("images")[image_content.image_id] = image_content.dict()

            # Translate and replace text
            translated_contents = []
            for target_language in request.target_languages:
                self.ctx.logger.info(f"Translating to {target_language.value}")
                translated_text = self.image_processor.translate_text(
                    image_content.extracted_text, request.source_language, target_language
                )
                self.ctx.logger.info(f"Translated text: {translated_text}")
                edited_image_path = self.image_processor.replace_text_in_image(
                    request.image_path, image_content.extracted_text, translated_text,
                    request.font_style or {"family": "arial.ttf", "size": "24", "color": "#000000"}
                )
                self.ctx.logger.info(f"Edited image saved: {edited_image_path}")
                translated_content = TranslatedContent.create(
                    image_content.image_id, target_language, translated_text, edited_image_path
                )
                translated_contents.append(translated_content)
                self.ctx.storage.get("translations")[f"{image_content.image_id}_{target_language.value}"] = translated_content.dict()

            return ProcessImageResponse(
                image_id=image_content.image_id,
                original_content=image_content,
                translated_contents=translated_contents
            )
        except Exception as e:
            self.ctx.logger.error(f"Error processing image: {e}")
            image_id = str(uuid.uuid4())
            return ProcessImageResponse(
                image_id=image_id,
                original_content=ImageContent(image_id=image_id, image_path=request.image_path, source_language=request.source_language, extracted_text="", timestamp=datetime.now().isoformat()),
                translated_contents=[],
                error=str(e)
            )

    async def schedule_posts(self, request: SchedulePostRequest) -> SchedulePostResponse:
        self.ctx.logger.info(f"Scheduling posts for image_id: {request.image_id}")
        try:
            schedules = self.scheduler.schedule_posts(
                request.image_id, request.platforms, request.language_time_zones, request.optimal_time
            )
            current_schedules = self.ctx.storage.get("schedules") or []
            current_schedules.extend([s.dict() for s in schedules])
            self.ctx.storage.set("schedules", current_schedules)
            self.ctx.logger.info(f"Scheduled {len(schedules)} posts")
            return SchedulePostResponse(schedules=schedules)
        except Exception as e:
            self.ctx.logger.error(f"Error scheduling posts: {e}")
            return SchedulePostResponse(schedules=[])

@content_translator.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info(f"Content Translator Agent started with address: {content_translator.address}")
    global AGENT_INSTANCE
    try:
        AGENT_INSTANCE = ContentTranslatorAgent(ctx)
    except Exception as e:
        ctx.logger.error(f"Failed to initialize agent instance: {e}")
        AGENT_INSTANCE = None

@translator_protocol.on_message(model=ProcessImageRequest, replies={ProcessImageResponse})
async def handle_process_image(ctx: Context, sender: str, msg: ProcessImageRequest):
    ctx.logger.info(f"Received request to process image from {sender}")
    global AGENT_INSTANCE
    if not AGENT_INSTANCE:
        ctx.logger.error("Agent instance not found")
        default_image_id = str(uuid.uuid4())
        await ctx.send(sender, ProcessImageResponse(
            image_id=default_image_id,
            original_content=ImageContent(image_id=default_image_id, image_path=msg.image_path, source_language=msg.source_language, extracted_text="", timestamp=datetime.now().isoformat()),
            translated_contents=[],
            error="Agent initialization failed"
        ))
        return
    response = await AGENT_INSTANCE.process_image(msg)
    await ctx.send(sender, response)

@translator_protocol.on_message(model=SchedulePostRequest, replies={SchedulePostResponse})
async def handle_schedule_post(ctx: Context, sender: str, msg: SchedulePostRequest):
    ctx.logger.info(f"Received request to schedule posts from {sender}")
    global AGENT_INSTANCE
    if not AGENT_INSTANCE:
        ctx.logger.error("Agent instance not found")
        await ctx.send(sender, SchedulePostResponse(schedules=[]))
        return
    response = await AGENT_INSTANCE.schedule_posts(msg)
    await ctx.send(sender, response)

content_translator.include(translator_protocol, publish_manifest=True)

if __name__ == "__main__":
    content_translator.run()