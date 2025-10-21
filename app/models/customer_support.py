import os, datetime, uuid
from sqlalchemy import Column, Boolean, Integer, String, ARRAY, DateTime, ForeignKey, Date, BigInteger
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableList

from app.models.model import Base


class CustomerSupportChatHistory(Base):
    
    __tablename__ = "customer_support_chat_history"
    
    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(String, unique=True)
    chat_history = Column(MutableList.as_mutable(ARRAY(JSONB)), default=[])
    name = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    agent_type =Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.timezone.utc))
    
class SmartCustomerSupportAgent(Base):
    
    __tablename__ = "smart_customer_support_chatbot"

    id = Column(String, default=uuid.uuid4, primary_key=True)
    bot_name = Column(String, nullable=False)
    role = Column(String, default="Energetic")
    personality = Column(String, default="Friendly")
    prompt = Column(String, nullable=False) 
    transfer_case = Column(JSONB, nullable=True)
    reference_file = Column(String, nullable=True)
    reference_text = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    
class SmartAgentIntegration(Base):
    
    __tablename__ = "smart_agent_integration"
    
    id = Column(String, default=uuid.uuid4, primary_key=True)
    selected_avatar_url = Column(String, nullable=False)
    agent_name = Column(String, nullable=False)
    colour = Column(String, nullable=False)
    domain = Column(MutableList.as_mutable(ARRAY(String)), default=[])
    first_message = Column(String, nullable=False)
    agent_id = Column(String, ForeignKey("smart_customer_support_chatbot.id", ondelete="CASCADE"))
    
class SmartBotAvatars(Base):
    
    __tablename__ = "smartbot_avatars"
    
    id = Column(String, default=uuid.uuid4, primary_key=True)
    avatar_url = Column(String, nullable=False)
    avatar_name = Column(String, nullable=True)
    user_id = Column(Integer, nullable=False)
    
class CustomerSupportIntegrationChats(Base):
    
    __tablename__ = "customer_support_chats"
    
    id = Column(String, primary_key=True, default=uuid.uuid4())
    chat_history = Column(MutableList.as_mutable(ARRAY(JSONB)), default=[])
    agent_id = Column(String, ForeignKey("smart_customer_support_chatbot.id", ondelete="CASCADE"))
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.timezone.utc))
    
    
    
    