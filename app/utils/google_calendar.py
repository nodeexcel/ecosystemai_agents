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
    
    url = "https://www.googleapis.com/calendar/v3/users/me/calendarList/primary"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    
    return response.json()
    
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
    
    return response


def get_freebusy_time(access_token):
    url = "https://www.googleapis.com/calendar/v3/freeBusy"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "timeMin": '2025-06-13T10:30:00',
        "timeMax": '2025-06-13T19:30:00',
        "timeZone": 'Asia/Kolkata',
        "items": [
            {
            "id": "primary"
            }
        ]
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    print(response.text)
    
    