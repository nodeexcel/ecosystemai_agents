from pydantic import BaseModel, Field
from typing import Union, Optional, Literal

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
    agent_language: str
    business_description: str = Field(min_length=50)
    your_business_offer: str =  Field(min_length=50)
    qualification_questions: list[str]
    sequence: Sequence
    objective_of_the_agent: Optional[str]
    calendar_choosed: Optional[str] = "calendly"
    webpage_link: Optional[str]
    webpage_type: Optional[str]
    reply_min_time: int
    reply_max_time: int
    is_followups_enabled: bool = False
    follow_up_details: FollowUPConfig
    emoji_frequency: int
    directness: int
    
class UpdateAppointmentSetterSchema(BaseModel):
    agent_name: Optional[str] = None
    agent_personality: Optional[str] = None
    agent_language: Optional[str] = None
    business_description: Optional[str] = Field(default=None, min_length=50)
    your_business_offer: Optional[str] =  Field(default=None, min_length=50)
    qualification_questions: Optional[list[str]] = None
    sequence: Optional[Sequence] = None
    objective_of_the_agent: Optional[str] = None
    calendar_choosed: Optional[str] = None
    webpage_link: Optional[str] = None
    webpage_type: Optional[str] = None
    reply_min_time: Optional[int] = None
    reply_max_time: Optional[int] = None
    is_followups_enabled: Optional[bool] = None
    follow_up_details: Optional[FollowUPConfig] = None
    emoji_frequency: Optional[int] = None
    directness: Optional[int] = None
    
class ChatWithAgent(BaseModel):
    message: str
    