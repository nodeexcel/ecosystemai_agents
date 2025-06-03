import os, datetime, uuid
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.models.model import Base



class Contacts(Base):
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    firstName = Column(String, nullable=True)
    lastName = Column(String, nullable=True)
    businessName = Column(String, nullable=True)
    companyName = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    created = Column(String, nullable=True)
    lastActivity =Column(String, nullable=True)
    status = Column(String, nullable=True)
    tags = Column(String, nullable=True)
    additionalEmails = Column(String, nullable=True)
    additionalPhones = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now())
    team_id = Column(String, ForeignKey("team.id", ondelete="CASCADE"))
    
class Lists(Base):
    __tablename__ = "lists"
    
    id = Column(Integer, primary_key=True, index=True)
    listName = Column(String, nullable=True)
    channel = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now())
    team_id = Column(String, ForeignKey("team.id", ondelete="CASCADE"))
    
class ContactLists(Base):
    __tablename__ = "contact_lists"
    
    id = Column(Integer, primary_key=True, index=True)
    contactid = Column(Integer, ForeignKey("contacts.id", ondelete="CASCADE"))
    lists_id = Column(Integer, ForeignKey("lists.id", ondelete="CASCADE"))