from datetime import datetime, timedelta
import pytz
from models import PostSchedule, Platform, Language, TimeZone

class PostScheduler:
    """
    Manages scheduling of posts based on audience time zones.
    """
    def schedule_posts(self, image_id: str, platforms: list[Platform], 
                      language_time_zones: dict[Language, TimeZone], 
                      optimal_time: str) -> list[PostSchedule]:
        """
        Schedule posts for each platform and language.
        """
        schedules = []
        optimal_hour, optimal_minute = map(int, optimal_time.split(":"))
        
        for platform in platforms:
            for language, time_zone in language_time_zones.items():
                # Get current time in the target time zone
                tz = pytz.timezone(time_zone.value)
                now = datetime.now(tz)
                
                # Schedule for the next day at the optimal time
                scheduled_time = now.replace(
                    hour=optimal_hour, minute=optimal_minute, second=0, microsecond=0
                ) + timedelta(days=1)
                
                schedules.append(PostSchedule(
                    image_id=image_id,
                    platform=platform,
                    target_language=language,
                    time_zone=time_zone,
                    scheduled_time=scheduled_time.isoformat()
                ))
        
        return schedules