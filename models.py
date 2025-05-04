from enum import Enum
from typing import List, Dict, Optional
from datetime import datetime
from uagents import Model

class Language(str, Enum):
    """
    Enum representing supported languages.
    """
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    CHINESE = "zh-cn"
    JAPANESE = "ja"

class TimeZone(str, Enum):
    """
    Enum representing target audience time zones.
    """
    UTC = "UTC"
    EST = "America/New_York"
    PST = "America/Los_Angeles"
    CET = "Europe/Paris"
    JST = "Asia/Tokyo"
    CST = "Asia/Shanghai"

class Platform(str, Enum):
    """
    Enum representing social media platforms.
    """
    INSTAGRAM = "instagram"
    TWITTER = "twitter"
    FACEBOOK = "facebook"

class ImageContent(Model):
    image_id: str
    image_path: str
    source_language: Language
    extracted_text: str
    timestamp: Optional[str] = None

    @classmethod
    def create(cls, image_id: str, image_path: str, source_language: Language, extracted_text: str, timestamp: Optional[str] = None):
        return cls(image_id=image_id, image_path=image_path, source_language=source_language, extracted_text=extracted_text, timestamp=timestamp)


class TranslatedContent(Model):
    """
    Model representing translated text for an image.
    """
    image_id: str
    target_language: Language
    translated_text: str
    edited_image_path: Optional[str] = None
    timestamp: str

    @classmethod
    def create(
        cls,
        image_id: str,
        target_language: Language,
        translated_text: str,
        edited_image_path: str = None
    ):
        return cls(
            image_id=image_id,
            target_language=target_language,
            translated_text=translated_text,
            edited_image_path=edited_image_path,
            timestamp=datetime.utcnow().isoformat()
        )

class PostSchedule(Model):
    """
    Model representing a scheduled post.
    """
    image_id: str
    platform: Platform
    target_language: Language
    time_zone: TimeZone
    scheduled_time: str  # ISO format
    post_status: str = "pending"

class ProcessImageRequest(Model):
    """
    Request model for processing an image (extract, translate, edit).
    """
    image_path: str
    source_language: Language
    target_languages: List[Language]
    font_style: Optional[Dict[str, str]] = None  # e.g., {"family": "Arial", "size": "24", "color": "#000000"}

class ProcessImageResponse(Model):
    """
    Response model for processed image.
    """
    image_id: str
    original_content: ImageContent
    translated_contents: List[TranslatedContent]
    error: Optional[str] = None  # Add error field

class SchedulePostRequest(Model):
    """
    Request model for scheduling posts.
    """
    image_id: str
    platforms: List[Platform]
    language_time_zones: Dict[Language, TimeZone]  # Maps languages to target time zones
    optimal_time: str = "18:00"  # Default posting time in local time zone

class SchedulePostResponse(Model):
    """
    Response model for scheduled posts.
    """
    schedules: List[PostSchedule]