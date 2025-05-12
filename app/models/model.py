import os
from sqlalchemy import Column, Boolean, Integer, String, Float, ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('SQLALCHEMY_DATABASE_URL')

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
    
class AppointmentSetter(Base):
    
    __tablename__ = "appointment_setter"

    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String, nullable=False)
    agent_personality = Column(String, nullable=False)
    agent_language = Column(String, default='English')
    business_description = Column(String, nullable=False)
    your_business_offer = Column(String, nullable=False)
    qualification_questions = Column(ARRAY(String), default=[])
    sequence = Column(JSONB, nullable=False)
    objective_of_the_agent = Column(ARRAY(String), nullable=False)
    calendar_choosed = Column(String, nullable=False)
    reply_min_time = Column(Integer, nullable=False)
    reply_max_time = Column(Integer, nullable=False)
    is_followups_enabled = Column(Boolean, default=False)
    follow_up_details = Column(JSONB, nullable=True)
    emoji_frequency = Column(Integer, nullable=False)
    directness = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)