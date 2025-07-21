import os, json
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent
from app.models.checkpointer_agent import async_checkpointer
from .email_agent import llm
    
async def initialise_agent(prompt):
    model = init_chat_model(
        "openai:gpt-4o",
        temperature=1,
    )
    
    content_creation_agent = create_react_agent(
        model=model,
        prompt=prompt,
        tools=[],
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