import os, datetime
from sqlalchemy import Column, Boolean, Integer, String, Float, ARRAY, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('SQLALCHEMY_DATABASE_URL')

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
    
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    firstName = Column(String(50), nullable=True)
    lastName = Column(String(50), nullable=True)
    phoneNumber = Column(String(20), nullable=True)
    image = Column(String(100), nullable=True)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=True)
    city = Column(String(30), nullable=True)
    company = Column(String(50), nullable=True)
    country = Column(String(50), nullable=True)
    role = Column(String(20), nullable=False, default='Admin')
    subscriptionType = Column(String(20), nullable=True)
    numberOfTeamMembers = Column(Integer, nullable=True, default=1)
    paymentId = Column(String(100), nullable=True)
    activeProfile = Column(Boolean, nullable=False, default=False)
    isProfileComplete = Column(Boolean, nullable=False, default=False)
    stripeCustomerId = Column(String(50), nullable=True)
    subscriptionStatus = Column(String(50), nullable=True)
    subscriptionId = Column(String(100), nullable=True)
    refreshToken = Column(String(255), nullable=True)
    otp = Column(String(6), nullable=True)
    subscriptionEndDate = Column(DateTime, nullable=True)
    subscriptionStartDate = Column(DateTime, nullable=True)
    subscriptionUpdatedAt = Column(DateTime, nullable=True)
    teamId = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now())
    

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
    objective_of_the_agent = Column(String, nullable=False)
    calendar_choosed = Column(String, nullable=True)
    webpage_link = Column(String, nullable=True)
    webpage_type = Column(String, nullable=True)
    reply_min_time = Column(Integer, nullable=False)
    reply_max_time = Column(Integer, nullable=False)
    is_followups_enabled = Column(Boolean, default=False)
    follow_up_details = Column(JSONB, nullable=True)
    emoji_frequency = Column(Integer, nullable=False)
    directness = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    user_id = Column(Integer, ForeignKey("users.id"))