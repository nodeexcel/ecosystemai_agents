import datetime
from fastapi import Depends
from fastapi.routing import APIRouter
from fastapi.responses import Response, RedirectResponse

from sqlalchemy.orm import Session

from app.models.get_db import get_db
from app.models.social_media_integrations import Google_Calendar
from app.utils.google_calendar import get_access_token, get_user_info, get_calendar, get_freebusy_time

router =  APIRouter(tags=['google-calendar'])

@router.get("/auth/google-calendar/callback")
def google_callback(code, state, db: Session = Depends(get_db)):
    
    response = get_access_token(code)
    state = int(state)
    
    if response.status_code != 200:
        return Response(content="Some error occured. Please react out to support or try again later.")   
    
    response = response.json()
    
    access_token = response.get("access_token")
    refresh_token = response.get("refresh_token")
    id_token = response.get("id_token")
    refresh_token_expires_in = response.get("refresh_token_expires_in")
    
    time_delta = datetime.timedelta(seconds=refresh_token_expires_in)
    
    expiry_time = datetime.datetime.now(datetime.timezone.utc) + time_delta
    
    user_info = get_user_info(id_token)
    
    name = user_info.get("name")
    email = user_info.get("email")
    google_id = user_info.get("sub")
    
    response = get_calendar(access_token)
    
    timezone = response.get('timeZone')
    
    calendar = db.query(Google_Calendar).filter_by(google_id=google_id).first()
    
    if calendar:
        calendar.access_token = access_token
        calendar.refresh_token = refresh_token
        calendar.name = name
        calendar.expiry_time = refresh_token_expires_in
    
    else:
        calendar = Google_Calendar(google_id=google_id, email=email, calendar_id='primary', name=name, access_token=access_token
                                , refresh_token=refresh_token, timezone=timezone, expiry_time=expiry_time, user_id=state)
        db.add(calendar)
        db.commit()
    get_freebusy_time(access_token)
    return RedirectResponse(url="http://116.202.210.102:3089/dashboard/brain", status_code=303)


    
    