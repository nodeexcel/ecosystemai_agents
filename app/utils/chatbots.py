from app.services.openai_service import llm
from app.prompts.prompts import summarizing_chat_for_title

async def summarizing_initial_chat(text):
    
    system_prompt = summarizing_chat_for_title(text)
    
    response = await llm.ainvoke([('system', system_prompt), ('human', text)])
    
    return response.content
    
    
    

