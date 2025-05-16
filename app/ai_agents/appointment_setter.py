import os, json
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Optional
from langchain_openai import ChatOpenAI

from psycopg_pool import ConnectionPool
from dotenv import load_dotenv

load_dotenv()



DB_URI = os.getenv("SQLALCHEMY_DATABASE_URL")

connection_kwargs = {
    "autocommit": True,
    "prepare_threshold": 0,
}

pool = ConnectionPool(
    conninfo=DB_URI,
    max_size=20,
    kwargs=connection_kwargs,
)
checkpointer = PostgresSaver(pool)

checkpointer.setup()

class AppointmentAgentResponse(BaseModel):
    response: str
    lead_qualification_status: Optional[str] = Field(description="status determined by agent only needed when agent is sure")
    
def initialise_agent(prompt, user_query):
    model = init_chat_model(
        "openai:gpt-4o",
        temperature=0,
    )
    
    appointment_agent = create_react_agent(
        model=model,
        tools=[book_meeting],
        prompt=prompt,
        checkpointer=checkpointer,
        response_format=AppointmentAgentResponse
    )
    
    return appointment_agent

def message_reply_by_agent(appointment_agent, user_query):
    
    config = {"configurable": {"thread_id": "101"}}
    response = appointment_agent.invoke({"messages": [{"role": "user", "content": user_query}]},
                                        config=config)
    structured_response= response["structured_response"]
    ai_response = response["messages"][-1].content
    
    return ai_response


@tool
def book_meeting():
    """return meeting timing"""
    return "5:30"
