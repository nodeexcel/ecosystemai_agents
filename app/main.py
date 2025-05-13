from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from sqlalchemy.orm import Session
from .models.model import AppointmentSetter, User
from .models.get_db import get_db 
from .schemas.appointment_setter import AppointmentSetterSchema
from .utils.user_auth import get_current_user

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,           
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/appointment-setter")
def create_appointment_setter_agent(payload: AppointmentSetterSchema, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    """This endpoint is used to create a appointmebt setter agent."""
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user eoes not exist"}, status_code=404)
    if payload.objective_of_the_agent == "web_page":
        if payload.webpage_link is None or payload.webpage_type is None:
            print(payload.webpage_link)
            print(payload.webpage_type )
            print("bbhbuhbbihj")
            return JSONResponse(content={'error': "Invalid data provided"}, status_code=422)
    appointment_setter = AppointmentSetter(**payload.model_dump(), user_id=user_id)
    db.add(appointment_setter)
    db.commit()
    db.refresh(appointment_setter)
    id = appointment_setter.id
    return JSONResponse(content={'success': f"Appointment agent with id {id} created successfullly."}, status_code=200)

@app.get("/appointment-setter-agents")
def get_appointment_setter_agents(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    """This endpoint all the agents."""
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user eoes not exist"}, status_code=404)
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

@app.get("/appointment-setter-agent-details/{agent_id}")
def get_appointment_setter_agent_details(agent_id, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    """This endpoint all the agents."""
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user eoes not exist"}, status_code=404)
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

@app.patch("/appointment-agent-status/{agent_id}")
def updating_status_of_appointment_agent(agent_id,  db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user eoes not exist"}, status_code=404)
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

@app.delete("/delete-appointment-agent/{agent_id}")
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
    

