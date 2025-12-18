import datetime, os
from fastapi import Depends
from fastapi.routing import APIRouter
from fastapi.responses import Response, RedirectResponse, JSONResponse

from sqlalchemy.orm import Session

from app.models.get_db import get_db
from app.models.model import User
from app.models.appointment_setter import AppointmentSetter
from app.models.social_media_integrations import GoogleCalendar
from app.utils.user_auth import get_current_user
from app.utils.google_calendar import get_access_token, get_user_info, get_calendar, get_freebusy_time, create_meeting

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
    
    items = get_calendar(access_token)
    
    for item in items:
        calendar_id = item.get('id')
    
        timezone = item.get('timeZone')
        
        
        calendar = db.query(GoogleCalendar).filter_by(calendar_id=calendar_id).first()
        
        if calendar:
            calendar.access_token = access_token
            calendar.refresh_token = refresh_token
            calendar.name = name
            
            time_delta = datetime.timedelta(seconds=refresh_token_expires_in)
            expiry_time = datetime.datetime.now(datetime.timezone.utc) + time_delta
            
            calendar.expiry_time = expiry_time
        
        else:
            calendar = GoogleCalendar(calendar_id=calendar_id, email=email, name=name, access_token=access_token
                                    , refresh_token=refresh_token, timezone=timezone, expiry_time=expiry_time, user_id=state)
            db.add(calendar)
            db.commit()
    return RedirectResponse(url= f"{os.getenv("FRONTEND_URL")}/dashboard/brain?tab=integration", status_code=303)

@router.get("/get-calendar-accounts")
def get_google_calendar_accounts(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)

    accounts = db.query(GoogleCalendar).filter_by(user_id=user_id).all()
    account_info = []
    for account in accounts:
        google_calendar_detail = {}
        google_calendar_detail['calendar_id'] = account.calendar_id
        account_info.append(google_calendar_detail)
    return JSONResponse(content={"google_calendar_info": account_info}, status_code=200)

@router.delete("/delete-google-calendar-account/{calendar_id}")
def delete_connected_insta_accounts(calendar_id, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    
    agent = db.query(AppointmentSetter).filter_by(calendar_id=calendar_id).first()
    if agent:
        return JSONResponse(content={"success": f"""The id is linked with {agent.agent_name}.
                                     Either delete agent or relink with another account."""}, status_code=400)

    account = db.query(GoogleCalendar).filter_by(calendar_id=calendar_id, user_id=user_id).first()
    if not account:
        return JSONResponse(content={"success": "Not authorized to delete the account"}, status_code=403)
    db.delete(account)
    db.commit()
    return JSONResponse(content={"success": "account deleted successfully"}, status_code=200)


    
    