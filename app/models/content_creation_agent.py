import os, datetime, uuid
from sqlalchemy import Column, Boolean, Integer, String, ARRAY, DateTime, ForeignKey, Date, BigInteger
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableList

from app.models.model import Base


class ContentCreationChatHistory(Base):
    
    __tablename__ = "content_creation_chat_history"
    
    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(String, unique=True)
    chat_history = Column(MutableList.as_mutable(ARRAY(JSONB)), default=[])
    name = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.timezone.utc))
    
class Content(Base):
    
    __tablename__ = "content"
    
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False)
    post_type = Column(String, nullable=False)
    language = Column(String, nullable=False)
    media_type = Column(String, nullable=False)
    video_duration = Column(String, nullable=True)
    author = Column(String, nullable=True)
    post_id = Column(String, nullable=False)
    post_status = Column(String, default="in_progress")
    caption = Column(String, nullable=True)
    media_urls = Column(ARRAY(JSONB), nullable=True)
    created_at = Column(DateTime, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"))
    
class LinkedInPost(Base):
    
    __tablename__ = "linkedin_post"
    
    id = Column(Integer, primary_key=True, index=True)
    generated_content = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    tone = Column(String, nullable=False)
    custom_instructions = Column(String, nullable=True)
    prompt = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False)
    user = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    
class XPost(Base):
    
    __tablename__ = "x_post"
    
    id = Column(Integer, primary_key=True, index=True)
    generated_content = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    purpose = Column(String, nullable=False)
    custom_instructions = Column(String, nullable=True)
    prompt = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False)
    user = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    
class YoutubeScript(Base):
    
    __tablename__ = "youtube_script"
    
    id = Column(Integer, primary_key=True, index=True)
    generated_content = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    custom_instructions = Column(String, nullable=True)
    prompt = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False)
    user = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    
    
    
    
    
    