import uuid, datetime
from fastapi import Depends, HTTPException
from fastapi.routing import APIRouter
from fastapi.responses import JSONResponse

from sqlalchemy.orm import Session

from app.models.model import User
from app.models.email_agent import EmailCampaign, EmailContent
from app.models.get_db import get_db 
from app.schemas.email_agent import EmailCampaignCreation, UpdateEmailCampaign, ContentCheck
from app.utils.user_auth import get_current_user
from app.ai_agents.prompts import Prompts
from app.ai_agents.email_agent import email_correction
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
        email_campaign.status = "draft"
    today = datetime.date.today()
    if today >= payload.start_date:
        email_campaign.status = "running"
    else:
        email_campaign.status = "scheduled"
    db.commit()
    return JSONResponse(content={'success': " Email Campaign is created successfullly."}, status_code=201)

@router.get("/get-email-campaigns")
def get_all_campaigns(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    """This endpoint all the campaigns."""
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    
    campaigns = db.query(EmailCampaign).filter_by(user_id=user_id).all()
    
    campaigns_info = []
    for campaign in campaigns:
        if campaign.start_date >= datetime.date.today() and campaign.is_draft == False and campaign.is_active == True:
            campaign.status = 'running'
            db.commit()
        start_date = campaign.start_date
        time = campaign.send_time_window
        sent = str(start_date) + " " + time
        campaign_info = {
            'campaign_id': campaign.id,
            'campaign_name': campaign.campaign_title,
            'sent': sent,
            'sent_to': 0,
            'campaign_status': campaign.status,
            'is_active': campaign.is_active
        }
        campaigns_info.append(campaign_info)
    return JSONResponse(content={'campaign_info': campaigns_info}, status_code=200)

@router.get("/campaign-details/{campaign_id}")
def get_campaign_details(campaign_id, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    """for getting single campign details."""
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    
    campaign = db.query(EmailCampaign).filter_by(id=campaign_id, user_id=user_id).first()
    
    if campaign:
        campaign_info = {
            'campaign_title': campaign.campaign_title,
            'campaign_objective': campaign.campaign_objective,
            'main_subject': campaign.main_subject,
            'cta_type': campaign.cta_type,
            'list_of_target': campaign.list_of_target,
            'desired_tone': campaign.desired_tone,
            'language': campaign.language,
            'send_time_window': campaign.send_time_window,
            'start_date': str(campaign.start_date),
            'frequency': campaign.frequency,
            'include_brainai': campaign.include_brainai,
            'include_branding': campaign.include_branding,
            'custom_prompt': campaign.custom_prompt,
            'text_length': campaign.text_length,
            'product_or_service_feature': campaign.product_or_service_feature,
            'review': campaign.review,
            'calender_choosed': campaign.calender_choosed,
            'url': campaign.url,
            'is_draft': campaign.is_draft,
            'file': ''
            }
        return JSONResponse(content={'campaign': campaign_info}, status_code=200)
    return JSONResponse(content={'error': 'Campaign does not exist'}, status_code=404)

@router.delete("/delete-campaign/{campaign_id}")
def deleting_campaign(campaign_id,  db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user eoes not exist"}, status_code=404)
    
    campaign = db.query(EmailCampaign).filter_by(id=campaign_id, user_id=user_id).first()
    
    if campaign:
        db.delete(campaign)
        db.commit()
        return JSONResponse(content={'success': 'Campaign deleted successfully'}, status_code=200)
    return JSONResponse(content={'error': 'Campaign does not exist'}, status_code=404)

@router.put("/update-campaign/{campaign_id}")
def update_email_campign(campaign_id, payload: UpdateEmailCampaign,  db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    
    if payload.cta_type == "book_a_meeting":
        if payload.calender_choosed is None:
            return JSONResponse(content={'error': "Need to provide calendar type"}, status_code=422)
        
    if payload.cta_type == "purchase" or "visit_a_page" or "reply":
        if payload.url is None:
            return JSONResponse(content={'error': "Need to provide url"}, status_code=422)
        
    campaign = db.query(EmailCampaign).filter_by(id=campaign_id, user_id=user_id).first()
    
    if campaign:
        email_campaign = payload.model_dump(exclude_unset=True)
        for key, value in email_campaign.items():
            setattr(campaign, key, value)
        db.commit()
        if payload.is_draft==True:
            campaign.status = "draft"
            db.commit()
        return JSONResponse(content={'success': 'Campaign updated successfully'}, status_code=200)
    return JSONResponse(content={'error': 'Not authorized to update this campaign'}, status_code=404)

@router.patch("/email-campaign-status/{campaign_id}")
def status_change_of_campaign(campaign_id,  db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    
    campaign = db.query(EmailCampaign).filter_by(id=campaign_id, user_id=user_id).first()
    
    today = datetime.date.today()
    if today >= campaign.start_date and campaign.status != "draft":
        campaign.status = "running"
        db.commit()
        
    if campaign.status != "draft" or campaign.status != "issue_detected":
        if campaign.is_active == False:
            if campaign.status == "paused":
                campaign.status = "scheduled"
            if campaign.status == "terminated":
                campaign.status = "running"
            campaign.is_active = True
            db.commit()
            return JSONResponse(content={'success': 'status updated for campaign'}, status_code=200)
        
        if campaign.is_active == True:
            if campaign.status == "scheduled":
                campaign.status = "paused"
            if campaign.status == "running":
                campaign.status = "terminated"
            campaign.is_active = False
            db.commit()
            return JSONResponse(content={'success': 'status updated for campaign'}, status_code=200)
    return JSONResponse(content={'error': 'Campaign does not exist'}, status_code=404)

@router.get("/get-campaign-schedule")
def get_campaign_schedule(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    
    campaigns = db.query(EmailCampaign).filter_by(user_id=user_id).all()
    if not campaigns:
        return JSONResponse(content={"Success": "You donot have any ongoing campaigns"}, status_code=200)
    
    schedule_info = []
    for campaign in campaigns:
        schedule_content_info = {}
        contents = db.query(EmailContent).filter(EmailContent.campaign_id == campaign.id).all()
        if not contents:
            schedule_content_info['campaign_id'] = campaign.id
            schedule_content_info['scheduled_days'] = campaign.frequency
            schedule_content_info['status'] = "planned"
            schedule_content_info['time'] = campaign.send_time_window
            schedule_content_info['name'] = campaign.campaign_title
            schedule_content_info['date'] = str(campaign.start_date)
            schedule_info.append(schedule_content_info)
            
        for content in contents:
            schedule_content_info['campaign_id'] = campaign.id
            schedule_content_info['date'] = str(content.scheduled_date)
            schedule_content_info['scheduled_days'] = campaign.frequency
            schedule_content_info['status'] = content.status
            schedule_content_info['time'] = content.scheduled_time
            schedule_content_info['name'] = campaign.campaign_title
            schedule_content_info['content_id'] = content.id
            schedule_info.append(schedule_content_info)
    return JSONResponse(content={"schedule_info": schedule_info}, status_code=200)

@router.get("/get-scheduled-content/{content_id}")
def get_scheduled_content(content_id, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    
    content = (db.query(EmailContent).join(EmailCampaign, EmailContent.campaign_id == EmailCampaign.id).
               join(User, EmailCampaign.user_id == User.id).
               filter(EmailContent.id == content_id, User.id == user_id)).first()
    if content:
        if content.status == 'approved' or content.status == 'pending_approval':
            return JSONResponse(content={"email": content.content})
    return JSONResponse(content={"error": "No content exits"}, status_code=404)


@router.post("/content-status/{content_id}")
def get_scheduled_content(content_id, payload: ContentCheck, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    
    content = (db.query(EmailContent).join(EmailCampaign, EmailContent.campaign_id == EmailCampaign.id).
               join(User, EmailCampaign.user_id == User.id).
               filter(EmailContent.id == content_id, User.id == user_id)).first()

    if content and content.status != "planned":
        if payload.status=="approved":
            content.status = "approved"
            content.is_approved = True
            db.commit()
            return JSONResponse(content="", status_code=200)
        if payload.status == "pending_approval":
            content.status = "pending_approval",
            content.content = payload.email_content
            db.commit()
            return JSONResponse(content="", status_code=200)
    return JSONResponse(content={"error": "Cannot edit the content"}, status_code=400)

@router.post("/duplicate-campaign/{campaign_id}")
def duplicate_a_campaign(campaign_id, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)  
    
    campaign = db.query(EmailCampaign).filter_by(id=campaign_id, user_id=user_id).first()
    
    if campaign:
        campaign_info = {
            'campaign_title': campaign.campaign_title,
            'campaign_objective': campaign.campaign_objective,
            'main_subject': campaign.main_subject,
            'cta_type': campaign.cta_type,
            'list_of_target': campaign.list_of_target,
            'desired_tone': campaign.desired_tone,
            'language': campaign.language,
            'send_time_window': campaign.send_time_window,
            'start_date': str(campaign.start_date),
            'frequency': campaign.frequency,
            'include_brainai': campaign.include_brainai,
            'include_branding': campaign.include_branding,
            'custom_prompt': campaign.custom_prompt,
            'text_length': campaign.text_length,
            'product_or_service_feature': campaign.product_or_service_feature,
            'review': campaign.review,
            'calender_choosed': campaign.calender_choosed,
            'url': campaign.url,
            'is_draft': campaign.is_draft,
            'status': campaign.status,
            'is_active': campaign.is_active
            }
                
        new_campaign = EmailCampaign(**campaign_info, user_id=user_id)
        db.add(new_campaign)
        db.commit()
        return JSONResponse(content={'success': "campaign duplicated"}, status_code=201)
    return JSONResponse(content={'error': 'Campaign does not exist'}, status_code=404) 
     
@router.get("/campigns-stats")
def campaign_stats(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    
    running_campaigns = db.query(EmailCampaign).filter_by(status='running', user_id=user_id).count()
    scheduled_campaigns = db.query(EmailCampaign).filter_by(status='scheduled', user_id=user_id).count()
    terminated_campaigns = db.query(EmailCampaign).filter_by(status='terminated', user_id=user_id).count()
    issue_detected_Campaigns = db.query(EmailCampaign).filter_by(status='issue_detected', user_id=user_id).count()
    draft_campaigns = db.query(EmailCampaign).filter_by(status='draft', user_id=user_id).count()
    paused_campaigns = db.query(EmailCampaign).filter_by(status='paused', user_id=user_id).count()
    
    return JSONResponse(content={"running": running_campaigns,
                                 "scheduled": scheduled_campaigns,
                                 "terminated": terminated_campaigns,
                                 "issue_detected": issue_detected_Campaigns,
                                 "draft": draft_campaigns,
                                 "paused": paused_campaigns}, status_code=200)


        
    
    
