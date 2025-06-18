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
        tools=[book_meeting, get_calendar_schedule],
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
def book_meeting(calendar_id, start_time, end_time, email, summary, description):
    """schedule a meeting with the client.
    calendar_id is the id of the calendar integrated
    start_time is the start time of time meeting finally available and decided format YYYY-MM--DDTHH:MM::SSZ
    end_time usually keeo it after 30 mins from start time or with nay other preference format YYYY-MM--DDTHH:MM::SSZ
    email is the recipient email id
    summary is the heading of the meeting it is about what meeting is scheduled and should be in 4-5 words maxx.
    description is the 10-15 words description about what the meeting is for and what it will do."""
    db = SessionLocal()
    calendar = db.query(GoogleCalendar).filter_by(calendar_id=calendar_id).first()
    access_token = calendar.access_token
    response = create_meeting(calendar_id, access_token, start_time, end_time, email, summary, description)
    
    if response.status_code == 401:
        response = refresh_access_token(calendar.refresh_token)
        calendar.access_token = response.get('access_token')
        db.commit()
        response = create_meeting(access_token, calendar_id, start_time, end_time, email, summary, description)
        
        print(response.text)
        
        if response.status_code == 200:
            return "success"


@tool
def get_calendar_schedule(calendar_id: str, date: str)-> list:
    """This function is only to check the busy schedule of the client and to check if any meeting is schedules or not.
    This will completely tell about all the meetings that are schduled for the day and is busy time.
    calendar_id is the id of the calendar integrated
    date is given by the user for scheduling in YYYY-MM-DD
    
    Output: It returns the busy time in a day like on ehat time calls are already scheduled. So if it is empty it does mean that whole day is available to schdue a call."""
    
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