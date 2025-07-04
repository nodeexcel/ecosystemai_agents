import os, datetime, uuid
from sqlalchemy import Column, Boolean, Integer, String, Float, ARRAY, DateTime, ForeignKey, Date

from .model import Base

class EmailCampaign(Base):
    __tablename__ = "email_campaign"
    
    id = Column(Integer, primary_key=True, index=True)
    campaign_title = Column(String, nullable=False)
    campaign_objective = Column(String, nullable=False)
    main_subject = Column(String, nullable=False)
    cta_type = Column(String, nullable=False)
    list_of_target = Column(ARRAY(Integer), nullable=False)
    desired_tone = Column(String, nullable=False)
    language = Column(String, nullable=False)
    send_time_window = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    frequency = Column(ARRAY(String), default=[])
    include_brainai = Column(Boolean, default=False)
    include_branding = Column(Boolean, default=False)
    custom_prompt = Column(String, nullable=True)
    text_length = Column(String, nullable=False)
    product_or_service_feature = Column(String, nullable=False)
    review = Column(Boolean, default=False)
    calender_choosed = Column(String, nullable=True)
    url = Column(String, nullable=False)
    is_draft = Column(Boolean, default=False)
    status = Column(String, default="scheduled")
    is_active = Column(Boolean, default=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    
class EmailContent(Base):
    __tablename__ = "email_content"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)
    is_approved = Column(Boolean, default=False)
    scheduled_date = Column(Date, nullable=False)
    scheduled_time = Column(String, nullable=False)
    is_sent = Column(Boolean, default=False)
    status = Column(String, default="planned")
    campaign_id = Column(Integer, ForeignKey("email_campaign.id", ondelete="CASCADE"))