import os, json
from langchain.chat_models import init_chat_model
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool


from dotenv import load_dotenv

load_dotenv()

DB_URI = os.getenv("SQLALCHEMY_DATABASE_URL")

connection_kwargs = {
    "autocommit": True,
    "prepare_threshold": 0,
}

async_pool = AsyncConnectionPool(DB_URI, kwargs=connection_kwargs)

checkpointer = AsyncPostgresSaver(async_pool)

llm = ChatOpenAI(
    model="gpt-4o",
    api_key=os.getenv("API_KEY"),
    temperature=1.5,
    top_p=0.7
)
    
async def initialise_agent(prompt):
    model = init_chat_model(
        "openai:gpt-4o",
        temperature=1,
    )
    
    account_agent = create_react_agent(
        model=model,
        prompt=prompt,
        tools=[],
        checkpointer=checkpointer,
    )
    
    return account_agent

async def message_reply_by_agent(account_agent, user_query, thread_id):
    config = {"configurable": {"thread_id": thread_id}}
    response = account_agent.ainvoke({"messages": [{"role": "user", "content": user_query}]},
                                        config=config)
    response = await response
    ai_response = response["messages"][-1].content
    
    return ai_response


async def check_message(prompt, user_query):
    response =  await llm.ainvoke([("system", prompt), ("human", user_query)])
    ai_response = response.content
    
    return ai_response