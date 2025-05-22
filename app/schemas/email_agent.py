from pydantic import BaseModel, Field
from typing import Union, Optional, Literal
from datetime import date

class EmailCampaignCreation(BaseModel):
    campaign_title: str
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
    review: bool
    calender_choosed: Optional[str] = None
    url: Optional[str]  = None
    is_draft: bool = False