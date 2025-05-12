from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .models.model import AppointmentSetter 
from .models.get_db import get_db 
from .schemas.appointment_setter import AppointmentSetterSchema
from fastapi.responses import JSONResponse
app = FastAPI()

@app.post("/appointment-setter")
def create_appointment_setter_agent(payload: AppointmentSetterSchema, db: Session = Depends(get_db)):
    """This endpoint is used to create a appointmebt setter agent."""
    appointment_setter = AppointmentSetter(**payload.dict())
    db.add(appointment_setter)
    db.commit()
    db.refresh(appointment_setter)
    return db.query(AppointmentSetter).all()

@app.get("/appointment-setter-agents")
def get_appointment_setter_agents(db: Session = Depends(get_db)):
    """This endpoint all the agents."""
    agents = db.query(AppointmentSetter).all()
    agents_info = []
    for agent in agents:
        agent_info = {
            'agent_id': agent.id,
            'agent_name': agent.agent_name,
            'is_active': agent.is_active
        }
        
        agents_info.append(agent_info)
    return JSONResponse(content={'agent': agents_info}, status_code=200)

@app.get("/appointment-setter-agent-details")
def get_appointment_setter_agent_details(db: Session = Depends(get_db)):
    """This endpoint all the agents."""
    agents = db.query(AppointmentSetter).all()
    agents_info = []
    for agent in agents:
        agent_info = {
            'agent_id': agent.id,
            'agent_name': agent.agent_name,
            'is_active': agent.is_active
        }
        
        agents_info.append(agent_info)
    return JSONResponse(content={'agent': agents_info}, status_code=200)
        
        

