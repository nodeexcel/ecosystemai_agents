from pydantic import BaseModel, Field
from typing import Union

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
    objective_of_the_agent: list[str]
    calendar_choosed: str
    reply_min_time: int
    reply_max_time: int
    is_followups_enabled: bool = False
    follow_up_details: FollowUPConfig
    emoji_frequency: int
    directness: int
    