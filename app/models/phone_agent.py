import datetime
from sqlalchemy import Column, String, Integer, ARRAY, Boolean, DateTime, ForeignKey

from app.models.model import Base

class AgentPhoneNumbers(Base):
    __tablename__ = "agent_phone_numbers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    country =  Column(String, nullable=False)
    phone_number = Column(String, nullable=False, unique=True)
    twilio_number = Column(String, nullable=False, unique=True)
    status = Column(Boolean, default=True)
    number_type = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now())
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    
class PhoneAgent(Base):
    __tablename__ = "phone_agent"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String, nullable=False)
    language = Column(String, nullable=False)
    status = Column(Boolean, default=True)
    voice = Column(String, nullable=False)
    phone_number = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    
class PhoneCampaign(Base):
    __tablename__ = "phone_campaign"
    
    id = Column(Integer, primary_key=True, index=True)
    campaign_name = Column(String, nullable=False)
    campaign_type = Column(String, nullable=True)
    language = Column(String, nullable=False)
    voice = Column(String, nullable=False)
    choose_calendar = Column(String, nullable=True)
    max_call_time = Column(Integer, nullable=True)
    target_lists = Column(Integer, nullable=False)
    country = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    status = Column(String, default="pending")
    catch_phrase = Column(String, nullable=False)
    call_script = Column(String, nullable=False)
    tom_engages = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.now())
    agent = Column(Integer, ForeignKey("phone_agent.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))

class CallRecord(Base):
    __tablename__ = "call_record"
    
    id = Column(Integer, primary_key=True, index=True)
    from_contact_number = Column(String, nullable=False) 
    contact_number = Column(String, nullable=False)
    result = Column(String, nullable=True)
    call_sid = Column(String, nullable=True)
    call_type = Column(String, nullable=True)
    campaign_name = Column(String, nullable=True)
    agent_name = Column(String, nullable=True)
    language = Column(String, nullable=True)
    voice = Column(String, nullable=True)
    user_id = Column(Integer, nullable=True)
    created_at = Column(String, default=datetime.datetime.now())
    
    
    
    