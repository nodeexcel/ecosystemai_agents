import datetime
from datetime import timedelta
from app.services.celery_app import celery_application
from app.models.get_db import SessionLocal
from sqlalchemy import or_ 
from app.models.email_agent import EmailCampaign, EmailContent
from app.ai_agents.prompts import Prompts
from app.ai_agents.email_agent import email_agent

@celery_application.task
def create_emails():
    db = SessionLocal()
    today_date = datetime.date.today()
    tomorrow_date = today_date + timedelta(hours=24)
    today = datetime.datetime.now()
    day = today + timedelta(hours=24)
    day = day.strftime("%A")
    campaigns = db.query(EmailCampaign).filter(or_(EmailCampaign.start_date == tomorrow_date,
                                EmailCampaign.frequency.any(day))).all()   
    for campaign in campaigns:
        content = db.query(EmailContent).filter_by(scheduled_date=tomorrow_date, campaign_id=campaign.id).all()
        if content or campaign.is_draft == True or campaign.is_active == False:
            pass
        else:
            scheduled_time = campaign.send_time_window
            prompt = Prompts.email_prompt_generator_agent(campaign)
            response = email_agent(prompt)
            if campaign.review == True:
                email_content = EmailContent(content=response, scheduled_date=tomorrow_date,
                                    scheduled_time=scheduled_time, campaign_id=campaign.id,
                                    status="pending_approval")
            if campaign.review == False:
                email_content = EmailContent(content=response, scheduled_date=tomorrow_date,
                                    scheduled_time=scheduled_time, is_approved=True, campaign_id=campaign.id,
                                    status="approved")
            db.add(email_content)
            db.commit()
        
        
        
    
@celery_application.task
def send_emails():
    try:
        db = SessionLocal()
        contents = db.query(EmailContent).filter(EmailContent.scheduled_date == datetime.date.today(), 
                                                EmailContent.scheduled_time=="9:00")
    finally:
        db.close()