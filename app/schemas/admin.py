from pydantic import BaseModel
from typing import Optional

class CreateUser(BaseModel):
    email: str
    role: str
    subscriptionType: str
    subscriptionStatus: str
    subscriptionDurationType: str
    
class SubscriptionUpdate(BaseModel):
    subscriptionType: str 
    subscriptionDurationType: str
    subscriptionStatus: Optional[str] = "active"
class CreditRequest(BaseModel):
    credits: int
