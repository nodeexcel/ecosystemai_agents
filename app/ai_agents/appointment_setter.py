import os, json
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Optional

from app.models.social_media_integrations import GoogleCalendar
from app.utils.google_calendar import get_freebusy_time, refresh_access_token, create_meeting
from app.models.model import SessionLocal


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
    
def initialise_agent(prompt):
    model = init_chat_model(
        "openai:gpt-4o",
        temperature=0,
    )
    
    appointment_agent = create_react_agent(
        model=model,
        tools=[get_busy_time],
        prompt=prompt,
        checkpointer=checkpointer,
        response_format=AppointmentAgentResponse
    )
    
    return appointment_agent

def message_reply_by_agent(appointment_agent, user_query, thread_id):
    
    config = {"configurable": {"thread_id": thread_id}}
    response = appointment_agent.invoke({"messages": [{"role": "user", "content": user_query}]},
                                        config=config)
    ai_response = response["messages"][-1].content
    ai_response = json.loads(ai_response)
    
    return ai_response


@tool
def get_busy_time(calendar_id: str, date: str)-> list:
    """This function is for getting the already busy or booked time of the calendar and hence you need to calculate free time.
    This will completely tell about all the meetings that are schduled for the day and is busy time.
    calendar_id is the id of the calendar integrated
    date is given by the user for scheduling in YYYY-MM-DD"""
    
    db = SessionLocal()
    calendar = db.query(GoogleCalendar).filter_by(calendar_id=calendar_id).first()
    
    access_token = calendar.access_token
    response = get_freebusy_time(access_token, calendar_id, date)
    if response.status_code == 401:
        response = refresh_access_token(calendar.refresh_token)
        calendar.access_token = response.get('access_token')
        db.commit()
        response = get_freebusy_time(calendar.access_token, calendar_id, date)
    response = response.json()
    busy_time = response["calendars"][calendar_id]['busy']
    
    return busy_time

@tool
def book_meeting():
    create_meeting()
