import os, datetime, uuid
from sqlalchemy import Column, Boolean, Integer, String, ARRAY, DateTime, ForeignKey, Date, BigInteger
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableList

from app.models.model import Base


class AccountChatHistory(Base):
    
    __tablename__ = "account_chat_history"
    
    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(String, unique=True)
    chat_history = Column(MutableList.as_mutable(ARRAY(JSONB)), default=[])
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    created_at = Column(DateTime, default= datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, default= datetime.datetime.now(datetime.timezone.utc))
