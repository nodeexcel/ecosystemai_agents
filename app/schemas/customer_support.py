from pydantic import BaseModel

class CreateSmartBotSchema(BaseModel):
    
    bot_name: str
    role: str
    personality: str
    prompt: str
    transfer_case: dict = {}
    reference_text: str
    use_ai_brain: bool = False
    
class CreateWebsiteLinkSchema(BaseModel):
    
    selected_avatar_url: str
    agent_name: str
    colour: str
    domain: list = []
    first_message: str
    agent_id: str

class UpdateSmartBotSchema(BaseModel):
    
    bot_name: str = None
    role: str = None
    personality: str = None
    prompt: str = None
    transfer_case: dict = None
    reference_text: str = None
    use_ai_brain: bool = False
    
class UpdateWebsiteLinkSchema(BaseModel):
    
    selected_avatar_url: str = None
    agent_name: str = None
    colour: str = None
    domain: list = None
    first_message: str = None
    agent_id: str = None
    
class Message(BaseModel):
    message: str

class PlatformIntegration(BaseModel):
    
    integration_platform: str = "Whatsapp"
    platform_id: str
    
    