from app.services.openai_service import llm
from app.ai_agents.prompts import Prompts

async def summarizing_initial_chat(text):
    
    system_prompt = Prompts.summarizing_chat_for_title(text)
    
    response = await llm.ainvoke([('system', system_prompt), ('human', text)])
    
    return response.content
    
    
    

