import os, datetime, uuid
from sqlalchemy import Column, Boolean, Integer, String, ARRAY, DateTime, ForeignKey, Date
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableList

from .model import Base

class AppointmentSetter(Base):
    __tablename__ = "appointment_setter"

    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String, nullable=False)
    agent_personality = Column(String, nullable=False)
    agent_language = Column(ARRAY(String))
    gender = Column(String, default="male")
    age = Column(Integer, nullable=False)
    business_description = Column(String, nullable=False)
    your_business_offer = Column(String, nullable=False)
    qualification_questions = Column(ARRAY(String), default=[])
    sequence = Column(JSONB, nullable=False)
    objective_of_the_agent = Column(String, nullable=False)
    calendar_choosed = Column(String, nullable=True)
    webpage_link = Column(String, nullable=True)
    whatsapp_number = Column(String, nullable=True)
    prompt = Column(String, nullable=False)
    is_followups_enabled = Column(Boolean, default=False)
    follow_up_details = Column(JSONB, nullable=True)
    emoji_frequency = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    
class AppointmentAgentLeads(Base):
    __tablename__ = "appointment_agent_leads"
    
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, unique=True)
    
class LeadAnalytics(Base):
    __tablename__ = "lead_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    chat_history = Column(MutableList.as_mutable(ARRAY(JSONB)), default=[])
    thread_id = Column(String, unique=True)
    agent_id = Column(Integer, ForeignKey("appointment_setter.id", ondelete="SET NULL"))
    lead_id = Column(Integer, ForeignKey("appointment_agent_leads.id", ondelete="SET NULL"))
    agent_is_enabled = Column(Boolean, default=True)
    status = Column(String, nullable=True)
    created_at = Column(Date, default=datetime.date.today())
    updated_at = Column(Date)
     
    