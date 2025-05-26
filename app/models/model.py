import os, datetime, uuid
from sqlalchemy import Column, Boolean, Integer, String, Float, ARRAY, DateTime, ForeignKey, Date
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableList
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
    role = Column(String(20), default='Admin')
    subscriptionType = Column(String(20), nullable=True)
    paymentId = Column(String(100), nullable=True)
    activeProfile = Column(Boolean,  default=False)
    isProfileComplete = Column(Boolean, default=False)
    stripeCustomerId = Column(String(50), nullable=True)
    subscriptionStatus = Column(String(50), nullable=True)
    subscriptionId = Column(String(100), nullable=True)
    refreshToken = Column(String(255), nullable=True)
    isDeleted = Column(Boolean, default=False)
    otp = Column(String(6), nullable=True)
    subscriptionEndDate = Column(DateTime, nullable=True)
    subscriptionStartDate = Column(DateTime, nullable=True)
    subscriptionUpdatedAt = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now())
    
class Team(Base):
    __tablename__ = "team"
    
    id = Column(String, primary_key=True)
    userId = Column(Integer, ForeignKey('users.id'))
    numberOfTeamMembers = Column(Integer, default=1)
    credits = Column(Integer, default=0)
    
    
class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True)
    email = Column(String(100), nullable=False)
    token = Column(String(255), unique=True, nullable=False)
    expiresAt = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now())


class TeamMember(Base):
    __tablename__ = "teammembers"

    id = Column(Integer, primary_key=True)
    isAdmin = Column(Boolean, default=False)
    role = Column(String(20), nullable=False)
    teamId = Column(String, ForeignKey('team.id'))
    userId = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.datetime.now())


class InviteToken(Base):
    __tablename__ = "invite_tokens"

    id = Column(Integer, primary_key=True)
    email = Column(String(100), nullable=False)
    token = Column(String(255), unique=True, nullable=False)
    userId = Column(Integer, ForeignKey('users.id'))
    teamId = Column(String, ForeignKey('team.id'))
    role = Column(String)
    expiresAt = Column(DateTime, nullable=False)
    accepted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.now())


class TransactionHistory(Base):
    __tablename__ = "transaction_history"

    id = Column(Integer, primary_key=True)
    userId = Column(Integer, ForeignKey('users.id'))
    paymentId = Column(String(100), nullable=False)
    amountPaid = Column(Float, nullable=False)
    email = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)
    paymentMethod = Column(String(50))
    subscriptionType = Column(String(20))
    receiptUrl = Column(String(255))
    currency = Column(String)
    transactionDate = Column(DateTime, default=datetime.datetime.now())
    created_at = Column(DateTime, default=datetime.datetime.now())
    
    
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
     
class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"
    
    id = Column(Integer, primary_key=True, index=True)
    data = Column(String, nullable=True)
    data_type = Column(String)
    path = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE")) 