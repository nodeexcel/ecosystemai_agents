import os, datetime, uuid
from sqlalchemy import Column, Boolean, Integer, String, ARRAY, DateTime, ForeignKey, Date, BigInteger
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableList

from app.models.model import Base


class SeoChatHistory(Base):
    
    __tablename__ = "seo_chat_history"
    
    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(String, unique=True)
    chat_history = Column(MutableList.as_mutable(ARRAY(JSONB)), default=[])
    name = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.timezone.utc))
