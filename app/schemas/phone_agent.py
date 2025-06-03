from pydantic import BaseModel, Field
from typing import Literal, Optional

class AddPhoneNumber(BaseModel):
    name: str
    phone_number: str
    country: str
    type: str
    status: bool = True

class CreatePhoneAgent(BaseModel):
    agent_name: str
    language: Literal['english', 'french']
    voice: str
    phone_number: str
    
class AddCampaigns(BaseModel):
    campaign_name: str
    language: str
    voice: str
    choose_calendar: Optional[str] = None
    max_call_time: int = Field(le=60)
    target_lists: list[str]
    agent: int
    country: str
    phone_number: str
    tom_engages: bool
    catch_phrase: str = Field(min_length=20)
    call_script: str = Field(min_length=50)    
    
class AgentFilterParams(BaseModel):
    country: Optional[str] = None
    language: Optional[str] = None
    voice: Optional[str] = None
    
class UpdateCampaign(BaseModel):
    campaign_name: Optional[str] = None
    language: Optional[str] = None
    voice: Optional[str] = None
    choose_calendar: Optional[str] = None
    max_call_time: Optional[int] = Field(default=None, le=60)
    target_lists: Optional[list[str]] = None
    agent: Optional[int] = None
    country: Optional[str] = None
    phone_number: Optional[str] = None
    tom_engages: Optional[bool] = False
    catch_phrase: Optional[str] = Field(default=None, min_length=20)
    call_script: Optional[str] = Field(default=None, min_length=50)  