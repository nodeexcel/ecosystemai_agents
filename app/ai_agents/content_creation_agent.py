import os, json
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent
from sqlalchemy import select
from app.models.model import  KnowledgeAttachment
from app.models.checkpointer_agent import async_checkpointer
from app.models.get_db import get_async_db
from app.utils.current_user import current_user
from .email_agent import llm


async def summarize_tools(filename: str | None = None) -> str:
    """
    Get summary of the file.
    
    If the user provide the filename, then get the summary for that file.
    Else fetch the summary for the latest processed file.
    
    Args:
        filename: Name of the file to fetch the summary
        
    Returns: Return the summary for given file id.
    """
    print("\nadfasdfasdfasd\n")
    user = current_user.get()
    print(f"Checking the current user:", user)
    print(f"Checking the current user id:", user.id)
    
    async with get_async_db() as db:
        content_attachment: KnowledgeAttachment | None = None
        
        if filename:
            print(f"Tool -> searching summary for filename: >{filename}<")
            result = await db.execute(
                select(KnowledgeAttachment)
                .where(KnowledgeAttachment.user_id == user.id)
                .where(KnowledgeAttachment.filename == filename)
                .order_by(KnowledgeAttachment.created_at.desc())
                .limit(1)
            )
            content_attachment = result.scalars().first()
            print("Tool -> ", result)
        else:
            print("Tool -> searching summary of latest file")
            result = await db.execute(
                select(KnowledgeAttachment)
                .where(KnowledgeAttachment.user_id == user.id)
                .order_by(KnowledgeAttachment.created_at.desc())
                .limit(1)
            )
            content_attachment = result.scalars().first()
            print("Tool -> ", result)
        
        if not content_attachment:
            return ""
        
        return content_attachment.file_summary
    
    
async def initialise_agent(prompt):
    model = init_chat_model(
        "openai:gpt-4o",
        temperature=1,
    )
    
    content_creation_agent = create_react_agent(
        model=model,
        prompt=prompt,
        tools=[summarize_tools],
        checkpointer=async_checkpointer,
    )
    
    return content_creation_agent

async def message_reply_by_agent(content_creation_agent, user_query, thread_id):
    config = {"configurable": {"thread_id": thread_id}}
    response = content_creation_agent.ainvoke({"messages": [{"role": "user", "content": user_query}]},
                                        config=config)
    response = await response
    ai_response = response["messages"][-1].content
    
    return ai_response

def text_content_generation(prompt):
    ai_message = llm.invoke([("system", prompt)])
    generated_prompt = ai_message.content
    ai_message = llm.invoke([("system", generated_prompt)])
    generated_content = ai_message.content
    return generated_prompt, generated_content