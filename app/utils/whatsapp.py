import os, requests, base64
from fastapi import HTTPException
from app.services.openai_service import openai_client

def generate_short_lived_access_token(code):
    
    params = {
        "client_id": os.getenv('FACEBOOK_CLIENT_ID'),
        "redirect_uri": os.getenv('FACEBOOK_REDIRECT_URI'),
        "client_secret": os.getenv('FACEBOOK_CLIENT_SECRET'),
        "code": code
    }
    
    response = requests.post("https://graph.facebook.com/v22.0/oauth/access_token", params=params)
    
    status = response.status_code
    response = response.json()
    
    return response, status

def long_lived_access_token(acceess_token):
    
    params = {
        'grant_type': "fb_exchange_token",
        'client_id': os.getenv('FACEBOOK_CLIENT_ID'),
        'client_secret': os.getenv('FACEBOOK_CLIENT_SECRET'),
        'fb_exchange_token': acceess_token
    }
    
    response = requests.get("https://graph.facebook.com/v22.0/oauth/access_token", params=params)
    
    status = response.status_code
    
    response = response.json()
    return response, status

def get_phone_number(access_token):
    
    params = {
        'access_token': access_token
    }
    
    response = requests.get("https://graph.facebook.com/v22.0/me/businesses", params=params)
    
    if response.status_code==200:
        response =  response.json()
        data = response["data"]
        data = data[0]
        business_id = data.get('id')
        
        response = requests.get(f"https://graph.facebook.com/v22.0/{business_id}/owned_whatsapp_business_accounts", params=params)
        
        if response.status_code==200:
            response = response.json()
            data = response["data"]
            data = data[0]
            whatsapp_business_id = data.get('id')
                
            response = requests.get(f"https://graph.facebook.com/v18.0/{whatsapp_business_id}/phone_numbers", params=params)
            if response.status_code==200:
                response = response.json()
                data = response["data"]
                data = data[0]
                
                return data, whatsapp_business_id
            
    return HTTPException(detail="no business account associated", status_code=400)
                
def whatsapp_send_messages(access_token, sender_phone_id, lead_id, response):
    
    url = f"https://graph.facebook.com/v22.0/{sender_phone_id}/messages"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    data = {
    "messaging_product": "whatsapp",
    "recipient_type": "individual",
    "to": lead_id,
    "type": "text",
    "text": {"body": response}
    }
    
    requests.post(url, headers=headers, json=data)
    
def invalid_whatsapp_send_messages(access_token, sender_phone_id, lead_id, response):
    
    url = f"https://graph.facebook.com/v22.0/{sender_phone_id}/messages"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    data = {
    "messaging_product": "whatsapp",
    "recipient_type": "individual",
    "to": lead_id,
    "type": "text",
    "text": {"body": "please send messages either in text or image for better understanding"}
    }
    
    requests.post(url, headers=headers, json=data)
    
def get_image_url(image_id, access_token):
    url = f"https://graph.facebook.com/v22.0/{image_id}"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    
    response = response.json()
    
    image_url = response.get('url')
    
    image_response = requests.get(image_url, headers=headers)

    image_encoded = base64.b64encode(image_response.content).decode('utf-8')
    
    return image_encoded
    
                
def image_to_text(encoded_image):
    response = openai_client.responses.create(
    model="gpt-4.1",
    input=[
        {
            "role": "user",
            "content": [
                { "type": "input_text", "text": "analyse the image and return a statement explaining what the image wants to pass as a message" },
                {
                    "type": "input_image",
                    "image_url": f"data:image/jpeg;base64,{encoded_image}",
                },
            ],
        }
    ],
)

    return response.output_text
        

        
