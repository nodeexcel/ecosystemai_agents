from datetime import datetime, date, time
from pydantic import BaseModel, Field
from typing import Optional, Literal

class NameUpdate(BaseModel):
    name: str


class PredisCheck(BaseModel):
    status: str
    post_id: str    
    caption: Optional[str] = None
    generated_media: Optional[list] = []
    
class ContentCreateSchema(BaseModel):
    text: str = Field(min_length=30)
    post_type: Literal['generic', 'quotes', 'meme']
    language: Literal['english', 'french']
    media_type: Literal['single_image', 'carousel', 'video']
    video_duration: Optional[str] = None
    author: Optional[str] = None
    created_at: datetime
    
class LinkedInPostSchema(BaseModel):
    topic: str
    custom_instructions: Optional[str] = None
    tone: Literal['professional', 'casual', 'friendly', 'formal', 'inspirational', 'humorous']
    created_at: datetime
    
class ContentUpdateSchema(BaseModel):
    content: str
    
class XPostSchema(BaseModel):
    topic: str
    custom_instructions: Optional[str] = None
    purpose: str
    created_at: datetime
    
class YoutubeScriptSchema(BaseModel):
    topic: str
    custom_instructions: Optional[str] = None
    created_at: datetime
    
