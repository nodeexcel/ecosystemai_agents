from pydantic import BaseModel, Field
from typing import Union, Optional, Literal
from datetime import date

class Sequence(BaseModel):
    trigger: str
    delay: int
    channel: str
    template: Union[str, None] = None
    
class FollowUPConfig(BaseModel):
    number_of_followups: Union[int, None] = None
    min_time: Union[int, None] = None
    max_time: Union[int, None] = None

class AppointmentSetterSchema(BaseModel):
    agent_name: str
    agent_personality: str
    agent_language: list[str]
    gender: str
    age: int
    prompt: str
    whatsapp_number: str
    business_description: str = Field(min_length=50)
    your_business_offer: str =  Field(min_length=50)
    platform_unique_id: str
    qualification_questions: list[str]
    sequence: Sequence
    objective_of_the_agent: Optional[str]
    calendar_choosed: Optional[str] = "google_calendar"
    calendar_id: Optional[str]
    webpage_link: Optional[str]
    is_followups_enabled: bool = False
    follow_up_details: FollowUPConfig
    emoji_frequency: int
    
class UpdateAppointmentSetterSchema(BaseModel):
    agent_name: Optional[str] = None
    agent_personality: Optional[str] = None
    agent_language: Optional[list[str]] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    prompt: Optional[str] = None
    business_description: Optional[str] = Field(default=None, min_length=50)
    your_business_offer: Optional[str] =  Field(default=None, min_length=50)
    qualification_questions: Optional[list[str]] = None
    sequence: Optional[Sequence] = None
    platform_unique_id: str = None
    objective_of_the_agent: Optional[str] = None
    calendar_choosed: Optional[str] = None
    calendar_id: Optional[str] = None
    webpage_link: Optional[str] = None
    whatsapp_number: Optional[str] = None
    is_followups_enabled: Optional[bool] = None
    follow_up_details: Optional[FollowUPConfig] = None
    emoji_frequency: Optional[int] = None
    
class ChatWithAgent(BaseModel):
    message: str
    chat_id: Optional[str] = None
    
class LeadAnalyticsSchema(BaseModel):
    date: date
    agent_id: str
    
class LeadStatus(BaseModel):
    lead_status: str = "positive"
    