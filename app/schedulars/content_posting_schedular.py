import os
from datetime import date, datetime, timezone
from app.services.celery_app import celery_application
from app.models.get_db import SessionLocal
from sqlalchemy import or_ 
from app.models.content_creation_agent import ScheduledContent
from app.models.social_media_integrations import Instagram, LinkedIn
from app.utils.instagram import publish_content_instagram
from app.utils.linkedin import publish_content_linkedin


@celery_application.task
def content_post():
    try:
        
        db = SessionLocal()
        current_date = date.today()
        current_time = datetime.now(timezone.utc).strftime('%H:%M:%S')
        
        scheduled_contents = db.query(ScheduledContent).filter_by(scheduled_date = current_date, scheduled_time = current_time
                                            , scheduled_type= "scheduled").all()
        
        
        for scheduled_content in scheduled_contents:
            if scheduled_content.platform == "instagram":
                
                instagram = db.query(Instagram).filter_by(instagram_user_id=scheduled_content.platform_unique_id).first()
                
                if not instagram:
                    continue
                
                media_url = os.getenv("S3_BASE_URL") + f"/{scheduled_content.document}"
                
                media_id = publish_content_instagram(instagram.access_token, instagram.refresh_token, scheduled_content.platform_unique_id, scheduled_content.media_type, media_url, scheduled_content.text)
            
            if scheduled_content.platform == "linkedin":
                
                linkedin = db.query(LinkedIn).filter_by(linkedin_id=scheduled_content.platform_unique_id).first()
                
                if not linkedin:
                    continue
                
                response, status_code = publish_content_linkedin(linkedin.access_token, linkedin.linkedin_id, scheduled_content.text)
                
                if status_code != 201:
                    continue

                media_id = response.get("x-restli-id")
            
            scheduled_content.media_id = media_id
            published_time = datetime.now(timezone.utc)
            scheduled_content.published_time = published_time
            db.commit()
            
    finally:
        db.close()