import os, datetime, uuid
from sqlalchemy import Column, Boolean, func, Integer, String, Float, ARRAY, DateTime, ForeignKey, Date
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('SQLALCHEMY_DATABASE_URL')
ASYNC_DATABASE_URL = os.getenv('ASYNC_DATABASE_URL')

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(
    bind=async_engine, class_=AsyncSession, autocommit=False, autoflush=False
)

Base = declarative_base()
    
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    firstName = Column(String(50), nullable=True)
    lastName = Column(String(50), nullable=True)
    phoneNumber = Column(String(20), nullable=True)
    image = Column(String(255), nullable=True)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=True)
    city = Column(String(30), nullable=True)
    company = Column(String(50), nullable=True)
    country = Column(String(50), nullable=True)
    role = Column(String(20), default='Admin')
    subscriptionType = Column(String(20), nullable=True)
    countryCode = Column(String(20), nullable=True)
    paymentId = Column(String(100), nullable=True)
    activeProfile = Column(Boolean,  default=False)
    isProfileComplete = Column(Boolean, default=False)
    stripeCustomerId = Column(String(50), nullable=True)
    subscriptionStatus = Column(String(50), nullable=True)
    subscriptionId = Column(String(100), nullable=True)
    refreshToken = Column(String(255), nullable=True)
    isDeleted = Column(Boolean, default=False)
    otp = Column(String(6), nullable=True)
    subscriptionDurationType = Column(String, nullable=True)
    subscriptionEndDate = Column(DateTime, nullable=True)
    subscriptionStartDate = Column(DateTime, nullable=True)
    subscriptionUpdatedAt = Column(DateTime, nullable=True)
    language = Column(String, default="english")
    created_at = Column(DateTime, default=datetime.datetime.now())
    
class Team(Base):
    __tablename__ = "team"
    
    id = Column(String, primary_key=True)
    userId = Column(Integer, ForeignKey('users.id'))
    numberOfTeamMembers = Column(Integer, default=1)
    creditRenewDate = Column(Date, nullable=True)
    numberOfRenewMonths = Column(Integer, nullable=True)
    nextMonthRenewDate = Column(Date, nullable=True)
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

     
class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"
    
    id = Column(Integer, primary_key=True, index=True)
    data = Column(String, nullable=True)
    data_type = Column(String)
    path = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE")) 
    created_at = Column(DateTime, default=datetime.datetime.now())

class AgentIntegrationTrack(Base):
    __tablename__ = "agent_integration_track"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_type = Column(String, nullable=False)
    integration_platform = Column(String, nullable=False)
    platform_id = Column(String, nullable=False)
    agent_id = Column(String, nullable=True)
    
    
class PhoneCredits(Base):
    __tablename__ = "phone_credits"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    balance = Column(Float, nullable=True)
    credits = Column(Float, nullable=True)

class KnowledgeAttachment(Base):
    
    __tablename__ = "knowledge_attachment"
    
    agent_name = Column(String, nullable=False)
    attachment_url = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    file_id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    file_summary = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE")) 