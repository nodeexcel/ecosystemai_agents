import uuid, datetime
from fastapi import Depends, HTTPException
from fastapi.routing import APIRouter
from fastapi.responses import JSONResponse

from sqlalchemy.orm import Session

from app.models.model import User
from app.models.email_agent import EmailCampaign
from app.models.get_db import get_db 
from app.schemas.email_agent import EmailCampaignCreation
from app.utils.user_auth import get_current_user
from app.ai_agents.prompts import Prompts
from app.utils.knowledge_base import fetch_text

router = APIRouter(tags=['email_campaign'])

@router.post("/email-campaign-creation")
def create_a_email_campaign(payload: EmailCampaignCreation, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    """This endpoint is used to create a email campaign."""
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    if payload.cta_type == "book_a_meeting":
        if payload.calender_choosed is None:
            return JSONResponse(content={'error': "Need to provide calendar type"}, status_code=422)
    if payload.cta_type == "purchase" or "visit_a_page" or "reply":
        if payload.url is None:
            return JSONResponse(content={'error': "Need to provide url"}, status_code=422)
    email_campaign = EmailCampaign(**payload.model_dump(), user_id=user_id)
    db.add(email_campaign)
    db.commit()
    db.refresh(email_campaign)
    if payload.is_draft==True:
        email_campaign.status = "Draft"
    today = datetime.date.today()
    if today == payload.start_date:
        email_campaign.status = "Running"
    else:
        email_campign.status = "Scheduled"
    db.commit()
    return JSONResponse(content={'success': f" Email Campaign is created successfullly."}, status_code=200)