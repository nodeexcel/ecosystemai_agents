import os, requests, jwt

def get_access_token(code):
    url = "https://oauth2.googleapis.com/token"
    
    params = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": os.getenv('GOOGLE_CLIENT_ID'),
        "client_secret": os.getenv('GOOGLE_CLIENT_SECRET'),
        "redirect_uri": os.getenv('GOOGLE_REDIRECT_URI')
    }
    
    response = requests.post(url, params=params)
    
    return response


def get_user_info(token: str):
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload
    except:
        return "invalid token"
    
    
def get_calendar(access_token):
    
    url = "https://www.googleapis.com/calendar/v3/users/me/calendarList"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    
    response = response.json()
    
    calendars_list = response.get('items')
    
    return calendars_list
    
def refresh_access_token(refresh_token):
    url = "https://oauth2.googleapis.com/token"
    
    params = {
        "grant_type": "refresh_token",
        "client_id": os.getenv('GOOGLE_CLIENT_ID'),
        "client_secret": os.getenv('GOOGLE_CLIENT_SECRET'),
        "refresh_token": refresh_token
    }
    
    response = requests.post(url, params=params)
    
    if response.status_code == 400:
        return "Authentication is needed again"
    
    return response.json()


def get_freebusy_time(access_token, calendar_id, date):
    url = "https://www.googleapis.com/calendar/v3/freeBusy"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    timeMin = date + "T9:00:00Z'"
    timeMax = date + "T19:30:00Z"
    
    payload = {
        "timeMin": timeMin,
        "timeMax": timeMax,
        "items": [
            {
            "id": calendar_id
            }
        ]
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    return response
    
def create_meeting(access_token, calendar_id):
    url = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "summary": "Meeting with Atul",
        "description": "Discussion on project updates.",
        "start": {
            "dateTime": "2025-06-13T15:00:00Z",
            "timeZone": "Asia/Kolkata"
        },
        "end": {
            "dateTime": "2025-06-13T16:00:00Z",
            "timeZone": "Asia/Kolkata"
        },
        "attendees": [
            { "email": "aayush.excel2011@gmail.com" }
        ],
        }
        
    response = requests.post(url, headers=headers, json=payload)
    
    print(response.text)