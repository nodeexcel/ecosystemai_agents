import os, requests
from fastapi import HTTPException
from app.services.openai_service import openai_client

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
    
    print(short_lived_access_token)
        
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
    
def instagram_message_invalid_type(access_token, recipient_id):
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
            "text": "Please do provide text or any image for better communication."
        }
    }
    
    response = requests.post(url, headers=headers, json=data)
    
def publish_content_instagram(access_token, refresh_token, instagram_user_id, media_type, media_url, caption):
    
    url = f"https://graph.instagram.com/v23.0/{instagram_user_id}/media"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    if media_type == "image":
        payload = {
            "caption": caption,
            "image_url": media_url
        }
        
    if media_type == "video":
        payload = {
            "caption": caption,
            "video_url": media_url
        }

    response = requests.post(url, headers=headers, data=payload)
    
    if response.status_code != 200:
        return HTTPException(detail="Could not publish content", status_code=500)
    response = response.json()
    
    container_id = response.get("id")
    
    url = f"https://graph.instagram.com/v23.0/{instagram_user_id}/media_publish"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    payload ={
        "creation_id": container_id 
    }
    
    response = requests.post(url, headers=headers, data=payload)
    
    if response.status_code != 200:
        return HTTPException(detail="Could not publish content", status_code=500)
    
    response = response.json()
    
    media_id = response.get("media_id")
    
    return media_id
    

def image_to_text(image_url):
    response = openai_client.responses.create(
    model="gpt-4.1-mini",
    input=[{
        "role": "user",
        "content": [
            {"type": "input_text", "text": "analyse the image and return a statement explaining what the image wants to pass as a message"},
            {
                "type": "input_image",
                "image_url": image_url,
            },
        ],
    }],
)
    return response.output_text
