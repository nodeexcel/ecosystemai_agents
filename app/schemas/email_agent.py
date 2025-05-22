from pydantic import BaseModel, Field
from typing import Union, Optional, Literal
from datetime import date

class EmailCampaignCreation(BaseModel):
    campaign_title: str
    campaign_objective: str
    main_subject: str
    cta_type: str
    list_of_target: list[str]
    desired_tone: str
    language: str
    send_time_window: str
    start_date: date
    frequency: Optional[list[str]] = []
    include_brainai: bool = False
    include_branding: bool = False
    custom_prompt: str
    text_length: str
    product_or_service_feature: str
    review: bool = False
    calender_choosed: Optional[str] = None
    url: Optional[str]  = None
    is_draft: bool = False
    
class UpdateEmailCampaign(BaseModel):
    campaign_title: Optional[str] = None
    campaign_objective: Optional[str] = None
    main_subject: Optional[str] = None
    cta_type: Optional[str] = None
    list_of_target: Optional[list[str]]
    desired_tone: Optional[str] = None
    language: Optional[str] = None
    send_time_window: Optional[str] = None
    start_date: Optional[date] = None
    frequency: Optional[list[str]] = []
    include_brainai: bool = False
    include_branding: bool = False
    custom_prompt: Optional[str] = None
    text_length: Optional[str] = None
    product_or_service_feature: Optional[str] = None
    review: Optional[bool] = False
    calender_choosed: Optional[str] = None
    url: Optional[str]  = None
    is_draft: bool = False