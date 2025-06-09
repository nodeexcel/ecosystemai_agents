from pydantic import BaseModel, Field
    
class InstagramCallback(BaseModel):
    code: str
    state: int
    
class InstagramMessageAlert(BaseModel):
    object: str
    entry: list