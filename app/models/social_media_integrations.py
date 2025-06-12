import datetime
from sqlalchemy import Column, String, Integer, ARRAY, Boolean, DateTime, ForeignKey

from app.models.model import Base

class Instagram(Base):
    
    __tablename__ = "instagram_connection_details"
    
    instagram_user_id = Column(String, primary_key=True)
    instagram_id = Column(String, primary_key=True)
    username = Column(String, nullable=False)
    name = Column(String, nullable=True)
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=True)
    expiry_time = Column(DateTime)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"))
    
class Whatsapp(Base):
    
    __tablename__ = "whatsapp_connection_details"
    
    whatsapp_business_id = Column(String, nullable=False)
    whatsapp_phone_id = Column(String, primary_key=True)
    phone_number = Column(String)
    name = Column(String, nullable=True)
    access_token = Column(String, nullable=False)
    expiry_time = Column(DateTime)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"))