from pydantic import BaseModel
from typing import Optional

class CreateUser(BaseModel):
    email: str
    password: str
    role: str
    subscriptionType: str
    subscriptionStatus: str
    subscriptionDurationType: str
    
class SubscriptionUpdate(BaseModel):
    subscriptionType: str  # "standard" or "pro"
    subscriptionStatus: Optional[str] = "active"
    
class CreditRequest(BaseModel):
    credits: int
