import datetime
from fastapi import Depends, HTTPException
from fastapi.routing import APIRouter
from fastapi.responses import JSONResponse

from sqlalchemy.orm import Session

from app.models.model import (User, Team, TeamMember)
from app.models.appointment_setter import AppointmentSetter, AppointmentAgentLeads, LeadAnalytics
from app.models.get_db import get_db 
from app.models.social_media_integrations import Instagram, Whatsapp
from app.schemas.appointment_setter import (AppointmentSetterSchema, UpdateAppointmentSetterSchema,
                                            ChatWithAgent, LeadAnalyticsSchema, LeadStatus)
from app.utils.user_auth import get_current_user
from app.ai_agents.prompts import Prompts
from app.ai_agents.appointment_setter import initialise_agent, message_reply_by_agent
from app.utils.instagram import instagram_send_message
from app.utils.whatsapp import whatsapp_send_messages
from app.utils.knowledge_base import fetch_text
from app.services.babel import get_translator_dependency

router = APIRouter(tags=['appointment_agent'])

@router.post("/appointment-setter")
def create_appointment_setter_agent(payload: AppointmentSetterSchema, db: Session = Depends(get_db),
                                user_id: str = Depends(get_current_user), _ = Depends(get_translator_dependency)):
    """This endpoint is used to create a appointment setter agent."""
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
    
    if payload.objective_of_the_agent == "book_a_meeting":
        if payload.calendar_choosed is None or payload.calendar_id is None:
            return JSONResponse(content={'error': _("Please provide calendar details")}, status_code=422)
    
    if payload.objective_of_the_agent == "web_page":
        if payload.webpage_link is None:
            return JSONResponse(content={'error': _("Please provide webpage details")}, status_code=422)
        
    trigger_platform = payload.sequence.trigger
        
    if trigger_platform != payload.sequence.channel:
        return JSONResponse(content={'error': _("Invalid data provided")}, status_code=422)
    
    connected_account = db.query(AppointmentSetter).filter_by(platform_unique_id=payload.platform_unique_id).first()
    if connected_account:
        return JSONResponse(content={'error': _("This account is already connected to a agent.")}, status_code=400)
    
    appointment_setter = AppointmentSetter(**payload.model_dump(), user_id=user_id)
    db.add(appointment_setter)
    db.commit()
    db.refresh(appointment_setter)
    id = appointment_setter.id
    return JSONResponse(content={'success': _(f"Appointment agent created successfullly.")}, status_code=200)

@router.get("/appointment-setter-agents")
def get_appointment_setter_agents(db: Session = Depends(get_db), user_id: str = Depends(get_current_user),
                                _ = Depends(get_translator_dependency)):
    """This endpoint all the agents."""
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
    
    agents = db.query(AppointmentSetter).filter_by(user_id=user_id).all()
    
    agents_info = []
    for agent in agents:
        sequence = agent.sequence
        channel = sequence.get('trigger')
        agent_info = {
            'agent_id': agent.id,
            'agent_name': agent.agent_name,
            'agent_channel': channel,
            'agent_language': agent.agent_language,
            'is_active': agent.is_active
        }
        agents_info.append(agent_info)
    return JSONResponse(content={'agent': agents_info}, status_code=200)

@router.get("/appointment-setter-agent-details/{agent_id}")
def get_appointment_setter_agent_details(agent_id, db: Session = Depends(get_db),
                                        user_id: str = Depends(get_current_user), _ = Depends(get_translator_dependency)):
    """This endpoint all the agents."""
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
    
    agent = db.query(AppointmentSetter).filter_by(id=agent_id, user_id=user_id).first()
    
    if agent:
        agent_info = {
            'agent_id': agent.id,
            'agent_name': agent.agent_name,
            'age': agent.age,
            'gender': agent.gender,
            'prompt': agent.prompt,
            'agent_personality': agent.agent_personality,
            'agent_language': agent.agent_language,
            'business_description': agent.business_description,
            'whatsapp_number': agent.whatsapp_number,
            'your_business_offer': agent.your_business_offer,
            'qualification_questions': agent.qualification_questions,
            'platform_unique_id': agent.platform_unique_id,
            'calendar_id': agent.calendar_id,
            'sequence': agent.sequence,
            'objective_of_the_agent': agent.objective_of_the_agent,
            'calendar_choosed': agent.calendar_choosed,
            'webpage_link': agent.webpage_link,
            'is_followups_enabled': agent.is_followups_enabled,
            'follow_up_details': agent.follow_up_details,
            'emoji_frequency': agent.emoji_frequency,
            }
        return JSONResponse(content={'agent': agent_info}, status_code=200)
    return JSONResponse(content={'error': _('Agent does not exist')}, status_code=404)

@router.patch("/appointment-agent-status/{agent_id}")
def updating_status_of_appointment_agent(agent_id,  db: Session = Depends(get_db),
                                        user_id: str = Depends(get_current_user), _ = Depends(get_translator_dependency)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
    
    agent = db.query(AppointmentSetter).filter_by(id=agent_id, user_id=user_id).first()
    if agent:
        if agent.is_active == False:
            agent.is_active = True
            chats = db.query(LeadAnalytics).filter_by(agent_id=agent.id).all()
            for chat in chats:
                chat.agent_is_enabled=True
            db.commit()
            return JSONResponse(content={'success': _('status updated for agent')}, status_code=200)
        
        if agent.is_active == True:
            agent.is_active = False
            chats = db.query(LeadAnalytics).filter_by(agent_id=agent.id).all()
            for chat in chats:
                chat.agent_is_enabled=False
            db.commit()
            return JSONResponse(content={'success': _('status updated for agent')}, status_code=200)
    return JSONResponse(content={'error': _('Agent does not exist')}, status_code=404)

@router.put("/update-appointment-agent/{agent_id}")
def updating_appointment_agent(agent_id, payload: UpdateAppointmentSetterSchema,  db: Session = Depends(get_db),
                            user_id: str = Depends(get_current_user), _ = Depends(get_translator_dependency)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
    
    if payload.objective_of_the_agent == "book_a_meeting":
        if payload.calendar_choosed is None or payload.calendar_id is None:
            return JSONResponse(content={'error': _("Please provide calendar details")}, status_code=422)
    
    trigger_platform = payload.sequence.trigger
        
    if trigger_platform != payload.sequence.channel:
        return JSONResponse(content={'error': _("Invalid data provided")}, status_code=422)
    
    connected_account = db.query(AppointmentSetter).filter_by(platform_unique_id=payload.platform_unique_id).first()
    if connected_account and connected_account.platform_unique_id != payload.platform_unique_id:
        return JSONResponse(content={'error': _("This account is already connected to a agent.")}, status_code=400)
    
    agent = db.query(AppointmentSetter).filter_by(id=agent_id, user_id=user_id).first()
    
    if agent:
        appointment_setter = payload.model_dump(exclude_unset=True)
        for key, value in appointment_setter.items():
            setattr(agent, key, value)
        db.commit()
        return JSONResponse(content={'success': _('Agent updated successfully')}, status_code=200)
    return JSONResponse(content={'error': _('Not authorized to update this agent')}, status_code=404)

@router.delete("/delete-appointment-agent/{agent_id}")
def deleting_appointment_agent(agent_id,  db: Session = Depends(get_db), user_id: str = Depends(get_current_user),
                               _ = Depends(get_translator_dependency)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
    
    agent = db.query(AppointmentSetter).filter_by(id=agent_id, user_id=user_id).first()
    
    if agent:
        db.delete(agent)
        db.commit()
        return JSONResponse(content={'success': _('Agent deleted successfully')}, status_code=200)
    return JSONResponse(content={'error': _('Not authorized to delete this agent')}, status_code=404)

@router.post("/chat-with-lead/{chat_id}")
def chatting_with_lead(chat_id, payload: ChatWithAgent, db: Session = Depends(get_db),
                       user_id: str = Depends(get_current_user), _ = Depends(get_translator_dependency)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
    
    chat = (db.query(LeadAnalytics).join(AppointmentSetter, LeadAnalytics.agent_id == AppointmentSetter.id)
                    .filter(AppointmentSetter.user_id == user_id,
                    LeadAnalytics.id == chat_id).first())
    
    if not chat:
        return JSONResponse(content={"error": _("chat does not exist")}, status_code=404)
        
    agent = db.query(AppointmentSetter).filter_by(id=chat.agent_id, user_id=user_id).first()
    
    if chat.agent_is_enabled == True:
        return JSONResponse(content={'error': _('Cannot talk to the lead presently agent enabled')}, status_code=400)

    chat_history = {}
    chat_history['agent'] = payload.message
    history = chat.chat_history
    history.append(chat_history)
    chat.chat_history = history
    chat.updated_at = datetime.date.today()
    db.commit()
    if chat.platform_unique_id != agent.platform_unique_id:
        return JSONResponse(content={"error": _("Cannot chat with lead as it was associated with a different platform before")}, status_code=400)
    sequence = agent.sequence
    platform = sequence.get('trigger')    
    if platform == 'Instagram':
        instagram = db.query(Instagram).filter_by(instagram_user_id=agent.platform_unique_id).first()
        access_token = instagram.access_token
        lead = db.query(AppointmentAgentLeads).filter_by(id=chat.lead_id).first()
        instagram_send_message(access_token, lead.lead_id, payload.message)
    if platform == 'Whatsapp':
        whatsapp = db.query(Whatsapp).filter_by(instagram_user_id=agent.platform_unique_id).first()
        access_token = whatsapp.access_token
        lead = db.query(AppointmentAgentLeads).filter_by(id=chat.lead_id).first()
        whatsapp_send_messages(access_token, whatsapp.whatsapp_phone_id, lead.lead_id, payload.message)
    return JSONResponse({"success": chat_history}, status_code=200)
    
@router.get("/get-chats")
def get_chat_history(lead_status: LeadStatus = Depends(), db: Session = Depends(get_db),
                     user_id: str = Depends(get_current_user), _ = Depends(get_translator_dependency)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
    
    agents = db.query(AppointmentSetter).filter_by(user_id=user_id).all()
    response = []
    if agents:
        for agent in agents:
            chats = db.query(LeadAnalytics).filter_by(agent_id=agent.id, status=lead_status.lead_status).all()
            if chats:
                for chat in chats:
                    lead = chat.id
                    response.append(lead)
        return JSONResponse(content={'success': response}, status_code=200)
    return JSONResponse(content={'error': _('No chat history')}, status_code=404)

@router.get("/get-chat-history/{chat_id}")
def get_chat_history(chat_id, db: Session = Depends(get_db),
                     user_id: str = Depends(get_current_user), _ = Depends(get_translator_dependency)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
    
    chat = db.query(LeadAnalytics).filter_by(id=chat_id).first()
    if chat:
        return JSONResponse(content={'chat': chat.chat_history, 
                                     'agent_is_enabled': chat.agent_is_enabled}, status_code=200)
    return JSONResponse(content={'error': _('No chat history')}, status_code=404)

@router.patch("/agent-status-for-chat/{chat_id}")
def change_agent_enabled_status(chat_id, db: Session = Depends(get_db),
                                user_id: str = Depends(get_current_user), _ = Depends(get_translator_dependency)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
    
    chat = (db.query(LeadAnalytics).join(AppointmentSetter, LeadAnalytics.agent_id == AppointmentSetter.id)
                    .filter(AppointmentSetter.user_id == user_id,
                    LeadAnalytics.id == chat_id).first())
    
    if chat:
        if chat.agent_is_enabled == False:
            chat.agent_is_enabled = True
            db.commit()
            return JSONResponse(content={'success': _('status updated for agent')}, status_code=200)
        
        if chat.agent_is_enabled == True:
            chat.agent_is_enabled = False
            db.commit()
            return JSONResponse(content={'success': _('status updated for agent')}, status_code=200)
    return JSONResponse(content={'error': _('Cannot change status of chat')}, status_code=404)

@router.get("/get-lead-analytics")
def get_lead_analytics(lead_params: LeadAnalyticsSchema = Depends(), db: Session = Depends(get_db),
                       user_id: str = Depends(get_current_user), _ = Depends(get_translator_dependency)):
    
    positive = 0
    negative = 0
    engaged = 0
    no_answer = 0
    total_leads = 0
    positive_rate = 0.00
    responded_rate = 0.00
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
    
    if lead_params.agent_id=='all':
        team_member = db.query(TeamMember).filter_by(userId=user_id).first()
        team = team_member.teamId
        if not team_member:
            return JSONResponse({"positive": positive, "negative": negative, "engaged": engaged
                         , "positive_rate": positive_rate, "responded_rate": responded_rate},
                    status_code=200)
            
        if lead_params.agent_id=='all':
            team_members = db.query(TeamMember).filter_by(teamId=team).all()
            
        for team_member in team_members:
            leads = (db.query(LeadAnalytics).join(AppointmentSetter, LeadAnalytics.agent_id == AppointmentSetter.id)
                    .filter(AppointmentSetter.user_id == team_member.userId,
                    LeadAnalytics.updated_at == lead_params.date).all())
            leads_per_user = (db.query(LeadAnalytics).join(AppointmentSetter, LeadAnalytics.agent_id == AppointmentSetter.id)
                    .filter(AppointmentSetter.user_id == team_member.userId, LeadAnalytics.updated_at == lead_params.date).count())
            total_leads = total_leads+leads_per_user
            for lead in leads:
                if lead.status=="positive":
                    positive = positive+1
                if lead.status=="negative":
                    negative=negative+1
                if lead.status=="engaged":
                    engaged=engaged+1
    else:
        agent_id = int(lead_params.agent_id)
        leads = db.query(LeadAnalytics).filter_by(agent_id=agent_id, updated_at=lead_params.date).all()
        total_leads = db.query(LeadAnalytics).filter_by(agent_id=agent_id, updated_at=lead_params.date).count()
        for lead in leads:
            if lead.status=="positive":
                positive = positive+1
            if lead.status=="negative":
                negative=negative+1
            if lead.status=="engaged":
                engaged=engaged+1
    if positive!=0 and total_leads!=0:
        positive_rate = (positive/total_leads)*100
    if total_leads!=0:
        responded = positive+negative+engaged
        responded_rate = (responded/total_leads*100)
    return JSONResponse({"positive": positive, "negative": negative, "engaged": engaged, "no_answer": no_answer
                         , "positive_rate": str(positive_rate), "responded_rate": str(responded_rate)}, status_code=200)
    
@router.post("/test-agent/{agent_id}")
def test_agent(agent_id, payload: ChatWithAgent, db: Session = Depends(get_db),
               user_id: str = Depends(get_current_user), _ = Depends(get_translator_dependency)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
    
    agent = db.query(AppointmentSetter).filter_by(id=agent_id, user_id=user_id).first()
    
    if not agent:
        return JSONResponse(content={"error": _("agent does not exist")}, status_code=404)
    
    thread_id = payload.chat_id
    if not thread_id:
        return JSONResponse(content={"error": _("test agent not configured properly")}, status_code=400)
    knowledge_base = fetch_text(payload.message, agent.user_id)
    prompt = Prompts.appointment_setter_prompt(agent, knowledge_base)
    appointment_agent = initialise_agent(prompt)
    ai_message = message_reply_by_agent(appointment_agent, payload.message, thread_id)
    response = ai_message.get('response')

    return JSONResponse({"response": response}, status_code=200)

        
        
        
    
    

