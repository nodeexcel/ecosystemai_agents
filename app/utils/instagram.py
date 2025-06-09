import os, requests

def user_authorization(code):

    authorize_data={
        "client_id": os.getenv("INSTAGRAM_CLIENT_ID"),
        "client_secret": os.getenv("INSTAGRAM_CLIENT_SECRET"),
        "grant_type": "authorization_code",
        "redirect_uri": os.getenv("INSTAGRAM_REDIRECT_URI"),
        "code": code}
    
    token_response = requests.post("https://api.instagram.com/oauth/access_token", data=authorize_data
    )
    
    status = token_response.status_code
    token_response = token_response.json()
    
    return token_response, status

def long_lived_access_token(short_lived_access_token):
    
    access_token_params = {
        "grant_type": "ig_exchange_token",
        "client_secret": os.getenv("INSTAGRAM_CLIENT_SECRET"),
        "access_token": short_lived_access_token}
    
    response =  requests.get("https://graph.instagram.com/access_token", params=access_token_params)
    
    status = response.status_code
    response = response.json()
    
    return response, status

def instagram_user_info(access_token):
    params = {"fields": "name, username, user_id",
              "access_token": access_token}
    
    user_response = requests.get("https://graph.instagram.com/v23.0/me", params = params)
    
    status = user_response.status_code
    user_response = user_response.json()
    
    return user_response, status

def instagram_send_message(access_token, recipient_id, message_text):
    url = f"https://graph.instagram.com/v23.0/me/messages"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    data = {
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    }
    
    response = requests.post(url, headers=headers, json=data)
