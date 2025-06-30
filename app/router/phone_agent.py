import uuid, datetime
from fastapi import Depends, HTTPException
from fastapi.routing import APIRouter
from fastapi.responses import JSONResponse, Response

from sqlalchemy.orm import Session

from app.models.model import User
from app.models.phone_agent import PhoneAgent, PhoneCampaign, AgentPhoneNumbers
from app.models.get_db import get_db 
from app.schemas.phone_agent import (AddPhoneNumber, CreatePhoneAgent,
                                     AddCampaigns, AgentFilterParams, UpdateCampaign)
from app.utils.user_auth import get_current_user
from twilio.twiml.voice_response import VoiceResponse
from app.services.babel import get_translator_dependency

router = APIRouter(tags=["phone-agents"])

@router.post("/add-phone-number")
def add_phone_number(payload: AddPhoneNumber, db: Session = Depends(get_db),
                     user_id: str = Depends(get_current_user), _ = Depends(get_translator_dependency)):
    
    """This endpoint is used to add a verified phone number."""
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
    
    phone_number = db.query(AgentPhoneNumbers).filter_by(phone_number=payload.phone_number, user_id=user_id).first()
    if phone_number:
        return JSONResponse(content={'error': _("phone number is already added")}, status_code=409)
        
    add_phone_number = AgentPhoneNumbers(**payload.model_dump(), user_id=user_id)
    db.add(add_phone_number)
    db.commit()
    db.refresh(add_phone_number)
    return JSONResponse(content={'success': _("Phone Number added to the list")}, status_code=201)

@router.post("/create-phone-agent")
def create_phone_agent(payload: CreatePhoneAgent, db: Session = Depends(get_db),
                       user_id: str = Depends(get_current_user), _ = Depends(get_translator_dependency)):
    
    """This endpoint is used to create a phone agent."""
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
    
    phone_number = db.query(AgentPhoneNumbers).filter_by(phone_number=payload.phone_number, user_id=user_id).first()
    if not phone_number:
        return JSONResponse(content={'error': _("phone number does not exists")}, status_code=404)
        
    add_agent = PhoneAgent(**payload.model_dump(), user_id=user_id)
    db.add(add_agent)
    db.commit()
    db.refresh(add_agent)
    return JSONResponse(content={'success': _("The phone agent is created successfully")}, status_code=201)

@router.post("/create-phone-campaign")
def create_phone_campaign(payload: AddCampaigns, db: Session = Depends(get_db),
                          user_id: str = Depends(get_current_user), _ = Depends(get_translator_dependency)):
    
    """This endpoint is used to create a phone agent campiagn."""
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
    
    phone_number = db.query(AgentPhoneNumbers).filter_by(phone_number=payload.phone_number, user_id=user_id).first()
    if not phone_number:
        return JSONResponse(content={'error': _("phone number does not exists")}, status_code=404)
    
    phone_number = db.query(PhoneAgent).filter_by(id=payload.agent, user_id=user_id).first()
    if not phone_number:
        return JSONResponse(content={'error': _("agent does not exists")}, status_code=404)
        
    add_campaign = PhoneCampaign(**payload.model_dump(), user_id=user_id)
    db.add(add_campaign)
    db.commit()
    db.refresh(add_campaign)
    return JSONResponse(content={'success': _("The phone agent is created successfully")}, status_code=201)

@router.get("/get-phone-numbers")
def get_phone_numbers(db: Session = Depends(get_db), user_id: str = Depends(get_current_user), _ = Depends(get_translator_dependency)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
    
    phone_numbers = db.query(AgentPhoneNumbers).filter_by(user_id=user_id).all()
    if not phone_numbers:
        return JSONResponse(content={'error': _("No Phone Numbers are added")}, status_code=404)
    
    numbers_info = []
    
    for phone_number in phone_numbers:
        number_data = {}
        number_data['id'] = phone_number.id
        number_data['phone_number'] = phone_number.phone_number
        number_data['country'] = phone_number.country
        number_data['status'] = phone_number.status
        number_data['total_calls'] = 0
        number_data['direction'] = phone_number.number_type
        number_data['creation_date'] = str(phone_number.created_at)
        numbers_info.append(number_data)
        
    return JSONResponse(content={'phone_numbers': numbers_info}, status_code=200)

@router.get("/get-phone-agents")
def get_phone_agents(params: AgentFilterParams = Depends(), db: Session = Depends(get_db),
                     user_id: str = Depends(get_current_user), _ = Depends(get_translator_dependency)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
    
    agents = db.query(PhoneAgent).filter_by(user_id=user_id).all()
    if not agents:
        return JSONResponse(content={'error': _("first create agents")}, status_code=404)
    
    agents_info = []
    
    for agent in agents:
        agent_data = {}
        agent_data['id'] = agent.id
        agent_data['agent_name'] = agent.agent_name
        agent_data['status'] = agent.status
        agent_data['language'] = agent.language
        agent_data['voice'] = agent.voice
        agent_data['phone_numbers'] = agent.phone_number
        agents_info.append(agent_data)
        
    return JSONResponse(content={'agents_info': agents_info}, status_code=200)

@router.get("/get-phone-campaigns")
def get_phone_campaigns(params: AgentFilterParams = Depends(), db: Session = Depends(get_db),
                        user_id: str = Depends(get_current_user), _ = Depends(get_translator_dependency)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
    
    campaigns = db.query(PhoneCampaign).filter_by(user_id=user_id).all()
    if not campaigns:
        return JSONResponse(content={'error': _("No campaigns created")}, status_code=404)
    
    campaigns_info = []
    
    for campaign in campaigns:
        campaign_data = {}
        agent = db.query(PhoneAgent).filter_by(id=campaign.agent).first()
        campaign_data['id'] = campaign.id
        campaign_data['campaign_name'] = campaign.campaign_name
        campaign_data['agent_name'] = agent.agent_name
        campaign_data['status'] = campaign.status
        campaign_data['language'] = campaign.language
        campaign_data['total_calls'] = 0
        campaign_data['creation_date'] = str(campaign.created_at)
        campaigns_info.append(campaign_data)
        
    return JSONResponse(content={'campaigns_info': campaigns_info}, status_code=200)

@router.get("/phone-campaign-detail/{campaign_id}")
def get_phone_campaign_detail(campaign_id, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
    
    campaign = db.query(PhoneCampaign).filter_by(id=campaign_id, user_id=user_id).first()
    if not campaign:
        return JSONResponse(content={'error': _("Campaign does not exist")}, status_code=404)
    
    campaign_data = {}
    agent = db.query(PhoneAgent).filter_by(id=campaign.agent).first()
    campaign_data['id'] = campaign.id
    campaign_data['campaign_name'] = campaign.campaign_name
    campaign_data['language'] = campaign.language
    campaign_data['voice'] = campaign.voice
    campaign_data['target_lists'] = campaign.target_lists
    campaign_data['choose_calendar'] = campaign.choose_calendar
    campaign_data['max_call_time'] = campaign.max_call_time
    campaign_data['agent'] = agent.id
    campaign_data['tom_engages'] = campaign.tom_engages
    campaign_data['phone_number'] = campaign.phone_number
    campaign_data['country'] = campaign.country
    campaign_data['catch_phrase'] = campaign.catch_phrase
    campaign_data['call_script'] = campaign.call_script
        
    return JSONResponse(content={'campaign_data': campaign_data}, status_code=200)

@router.patch("/phone-number-status/{phone_number_id}")
def updating_status_of_phone_number(phone_number_id,  db: Session = Depends(get_db),
                                    user_id: str = Depends(get_current_user), _ = Depends(get_translator_dependency)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
    
    number = db.query(AgentPhoneNumbers).filter_by(id=phone_number_id, user_id=user_id).first()
    if number:
        if number.status == False:
            number.status = True
            db.commit()
            return JSONResponse(content={'success': _('status updated for number')}, status_code=200)
        
        if number.status == True:
            number.status = False
            db.commit()
            return JSONResponse(content={'success': _('status updated for number')}, status_code=200)
    return JSONResponse(content={'error': _('Phone Number does not exist')}, status_code=404)

@router.patch("/phone-agent-status/{agent_id}")
def updating_status_of_phone_agent(agent_id,  db: Session = Depends(get_db),
                                   user_id: str = Depends(get_current_user), _ = Depends(get_translator_dependency)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
    
    agent = db.query(PhoneAgent).filter_by(id=agent_id, user_id=user_id).first()
    if agent:
        if agent.status == False:
            agent.status = True
            db.commit()
            return JSONResponse(content={'success': _('status updated for agent')}, status_code=200)
        
        if agent.status == True:
            agent.status = False
            db.commit()
            return JSONResponse(content={'success': _('status updated for agent')}, status_code=200)
    return JSONResponse(content={'error': _('Phone Number does not exist')}, status_code=404)

@router.delete("/phone-number/{phone_number_id}")
def delete_phone_number(phone_number_id,  db: Session = Depends(get_db), 
                        user_id: str = Depends(get_current_user), _ = Depends(get_translator_dependency)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
    
    number = db.query(AgentPhoneNumbers).filter_by(id=phone_number_id, user_id=user_id).first()
    if number:
        db.delete(number)
        db.commit()
        return JSONResponse(content={'success': _('Phone Number deleted successfully')}, status_code=200)
    return JSONResponse(content={'error': _('Phone Number does not exist')}, status_code=404)

@router.delete("/phone-campaign/{campaign_id}")
def delete_campaign(campaign_id,  db: Session = Depends(get_db), 
                    user_id: str = Depends(get_current_user), _ = Depends(get_translator_dependency)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
    
    campaign = db.query(PhoneCampaign).filter_by(id=campaign_id, user_id=user_id).first()
    if campaign:
        db.delete(campaign)
        db.commit()
        return JSONResponse(content={'success': _('Campaign deleted successfully')}, status_code=200)
    return JSONResponse(content={'error': _('Campaign does not exist')}, status_code=404)


@router.put("/update-phone-campaign/{campaign_id}")
def update_phone_campign(campaign_id, payload: UpdateCampaign,  db: Session = Depends(get_db),
                         user_id: str = Depends(get_current_user), _ = Depends(get_translator_dependency)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
        
    campaign = db.query(PhoneCampaign).filter_by(id=campaign_id, user_id=user_id).first()
    
    if campaign:
        phone_campaign = payload.model_dump(exclude_unset=True)
        for key, value in phone_campaign.items():
            setattr(campaign, key, value)
        db.commit()
        return JSONResponse(content={'success': _('Campaign updated successfully')}, status_code=200)
    return JSONResponse(content={'error': _('Not authorized to update this campaign')}, status_code=404)

@router.post("/duplicate-phone-campaign/{campaign_id}")
def duplicate_a_campaign(campaign_id, db: Session = Depends(get_db), user_id: str = Depends(get_current_user),
                         _ = Depends(get_translator_dependency)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)  
    
    campaign = db.query(PhoneCampaign).filter_by(id=campaign_id, user_id=user_id).first()
    
    if campaign:
        campaign_info = {
            "campaign_name": campaign.campaign_name,
            "language": campaign.language,
            "voice": campaign.voice,
            "choose_calendar": campaign.choose_calendar,
            "max_call_time": campaign.max_call_time,
            "target_lists": campaign.target_lists,
            "country": campaign.country,
            "phone_number": campaign.phone_number,
            "status": campaign.status,
            "catch_phrase": campaign.catch_phrase,
            "call_script": campaign.call_script,
            "agent": campaign.agent}
                
        new_campaign = PhoneCampaign(**campaign_info, user_id=user_id)
        db.add(new_campaign)
        db.commit()
        return JSONResponse(content={'success': _("campaign duplicated")}, status_code=201)
    return JSONResponse(content={'error': _('Campaign does not exist')}, status_code=404) 


    


