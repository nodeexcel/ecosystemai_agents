import uuid
from fastapi import Depends, HTTPException
from fastapi.routing import APIRouter
from fastapi.responses import JSONResponse

from sqlalchemy.orm import Session

from app.models.model import AppointmentSetter, User, KnowledgeBase, LeadAnalytics, AppointmentAgentLeads
from app.models.get_db import get_db 
from app.schemas.appointment_setter import AppointmentSetterSchema, UpdateAppointmentSetterSchema, ChatWithAgent
from app.utils.user_auth import get_current_user
from app.ai_agents.prompts import Prompts
from app.ai_agents.appointment_setter import initialise_agent, message_reply_by_agent

router = APIRouter(tags=['appointment_agent'])

@router.post("/appointment-setter")
def create_appointment_setter_agent(payload: AppointmentSetterSchema, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    """This endpoint is used to create a appointmebt setter agent."""
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    if payload.objective_of_the_agent == "web_page":
        if payload.webpage_link is None or payload.webpage_type is None:
            return JSONResponse(content={'error': "Invalid data provided"}, status_code=422)
    appointment_setter = AppointmentSetter(**payload.model_dump(), user_id=user_id)
    db.add(appointment_setter)
    db.commit()
    db.refresh(appointment_setter)
    id = appointment_setter.id
    return JSONResponse(content={'success': f"Appointment agent with id {id} created successfullly."}, status_code=200)

@router.get("/appointment-setter-agents")
def get_appointment_setter_agents(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    """This endpoint all the agents."""
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    agents = db.query(AppointmentSetter).filter_by(user_id=user_id).all()
    agents_info = []
    for agent in agents:
        agent_info = {
            'agent_id': agent.id,
            'agent_name': agent.agent_name,
            'is_active': agent.is_active
        }
        agents_info.append(agent_info)
    return JSONResponse(content={'agent': agents_info}, status_code=200)

@router.get("/appointment-setter-agent-details/{agent_id}")
def get_appointment_setter_agent_details(agent_id, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    """This endpoint all the agents."""
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    agent = db.query(AppointmentSetter).filter_by(id=agent_id, user_id=user_id).first()
    if agent:
        agent_info = {
            'agent_id': agent.id,
            'agent_name': agent.agent_name,
            'agent_personality': agent.agent_personality,
            'agent_language': agent.agent_language,
            'business_description': agent.business_description,
            'your_business_offer': agent.your_business_offer,
            'qualification_questions': agent.qualification_questions,
            'sequence': agent.sequence,
            'objective_of_the_agent': agent.objective_of_the_agent,
            'calendar_choosed': agent.calendar_choosed,
            'webpage_link': agent.webpage_link,
            'webpage_type': agent.webpage_type,
            'reply_min_time': agent.reply_min_time,
            'reply_max_time': agent.reply_max_time,
            'is_followups_enabled': agent.is_followups_enabled,
            'follow_up_details': agent.follow_up_details,
            'emoji_frequency': agent.emoji_frequency,
            'directness': agent.directness
            }
        return JSONResponse(content={'agent': agent_info}, status_code=200)
    return JSONResponse(content={'error': 'Agent does not exist'}, status_code=404)

@router.patch("/appointment-agent-status/{agent_id}")
def updating_status_of_appointment_agent(agent_id,  db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    agent = db.query(AppointmentSetter).filter_by(id=agent_id, user_id=user_id).first()
    if agent:
        if agent.is_active == False:
            agent.is_active = True
            db.commit()
            return JSONResponse(content={'success': 'status updated for agent'}, status_code=200)
        if agent.is_active == True:
            agent.is_active = False
            db.commit()
            return JSONResponse(content={'success': 'status updated for agent'}, status_code=200)
    return JSONResponse(content={'error': 'Agent does not exist'}, status_code=404)

@router.put("/update-appointment-agent/{agent_id}")
def updating_appointment_agent(agent_id, payload: UpdateAppointmentSetterSchema,  db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    agent = db.query(AppointmentSetter).filter_by(id=agent_id, user_id=user_id).first()
    if agent:
        appointment_setter = payload.model_dump(exclude_unset=True)
        for key, value in appointment_setter.items():
            setattr(agent, key, value)
        db.commit()
        return JSONResponse(content={'success': 'Agent updated successfully'}, status_code=200)
    return JSONResponse(content={'error': 'Not authorized to update this agent'}, status_code=404)

@router.delete("/delete-appointment-agent/{agent_id}")
def deleting_appointment_agent(agent_id,  db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user eoes not exist"}, status_code=404)
    agent = db.query(AppointmentSetter).filter_by(id=agent_id, user_id=user_id).first()
    if agent:
        db.delete(agent)
        db.commit()
        return JSONResponse(content={'success': 'Agent deleted successfully'}, status_code=200)
    return JSONResponse(content={'error': 'Not authorized to delete this agent'}, status_code=404)

@router.post("/chat-with-agent/{agent_id}")
def chatting_with_agent(agent_id, payload: ChatWithAgent, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    lead = db.query(AppointmentAgentLeads).filter_by(lead_id=str(user_id)).first()
    if not lead:
        lead = AppointmentAgentLeads(lead_id=user_id)
        db.add(lead)
        db.commit()
        db.refresh(lead)
    agent = db.query(AppointmentSetter).filter_by(id=agent_id, user_id=user_id).first()
    if not agent:
        return JSONResponse(content={'error': 'Not authorized to talk this agent'}, status_code=404)
    lead_chat = db.query(LeadAnalytics).filter_by(lead_id=user_id, agent_id=agent_id).first()
    chat_history = {}
    chat_history['user'] = payload.message
    if not lead_chat:
        thread_id = uuid.uuid4()
        lead_chat = LeadAnalytics(lead_id=user_id, agent_id=agent_id, thread_id=thread_id)
        db.add(lead_chat)
        db.commit()
        db.refresh(lead_chat)
    if lead_chat:
        thread_id = lead_chat.thread_id
        db.commit()
    chat = lead_chat.chat_history
    chat.append(chat_history)
    lead_chat.chat_history = chat
    db.commit()
    knowledge_base = db.query(KnowledgeBase).filter_by(id=user_id).first()
    knowledge_base = knowledge_base.data
    prompt = Prompts.appointment_setter_prompt(agent, knowledge_base)
    appointment_agent = initialise_agent(prompt)
    ai_message = message_reply_by_agent(appointment_agent, payload.message, thread_id)
    response = ai_message.get('response')
    chat_history = {}
    chat_history['agent'] = response
    chat = lead_chat.chat_history
    lead_chat.status = ai_message.get('lead_qualification_status')
    chat.append(chat_history)
    lead_chat.chat_history = chat
    db.commit()
    return JSONResponse({"success": chat_history}, status_code=200)
    
@router.get("/get-chats")
def get_chat_history(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    agents = db.query(AppointmentSetter).filter_by(user_id=user_id).all()
    response = []
    if agents:
        for agent in agents:
            chats = db.query(LeadAnalytics).filter_by(agent_id=agent.id).all()
            if chats:
                for chat in chats:
                    lead = chat.id
                    response.append(lead)
        return JSONResponse(content={'success': response}, status_code=200)
    return JSONResponse(content={'error': 'No chat history'}, status_code=404)

@router.get("/get-chat-history/{chat_id}")
def get_chat_history(chat_id, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    chat = db.query(LeadAnalytics).filter_by(id=chat_id).first()
    if chat:
        return JSONResponse(content={'success': chat.chat_history}, status_code=200)
    return JSONResponse(content={'error': 'No chat history'}, status_code=404)
        
    

