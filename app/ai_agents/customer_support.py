import os, json
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent
from app.models.checkpointer_agent import async_checkpointer
    
async def initialise_agent(prompt):
    model = init_chat_model(
        "openai:gpt-4o",
        temperature=1,
    )
    
    customer_agent = create_react_agent(
        model=model,
        prompt=prompt,
        tools=[],
        checkpointer=async_checkpointer,
    )
    
    return customer_agent

async def message_reply_by_agent(customer_agent, user_query, thread_id):
    config = {"configurable": {"thread_id": thread_id}}
    response = customer_agent.ainvoke({"messages": [{"role": "user", "content": user_query}]},
                                        config=config)
    response = await response
    ai_response = response["messages"][-1].content
    
    return ai_response

def sync_initialise_agent(prompt):
    model = init_chat_model(
        "openai:gpt-4o",
        temperature=1,
    )
    
    customer_agent = create_react_agent(
        model=model,
        prompt=prompt,
        tools=[],
        checkpointer=async_checkpointer,
    )
    
    return customer_agent

def sync_message_reply_by_agent(customer_agent, user_query, thread_id):
    config = {"configurable": {"thread_id": thread_id}}
    response = customer_agent.invoke({"messages": [{"role": "user", "content": user_query}]},
                                        config=config)
    response = response
    ai_response = response["messages"][-1].content
    
    return ai_response