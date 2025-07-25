import os, requests

def generate_access_token(code):
    
    url = "https://www.linkedin.com/oauth/v2/accessToken"
    
    param = {"grant_type": "authorization_code",
    "code": code,
    "client_id": os.getenv("LINKEDIN_CLIENT_ID"),
    "client_secret": os.getenv("LINKEDINCLIENT_SECRET"),
    "redirect_uri": os.getenv("LINKEDIN_REDIRECT_URI")}
    
    response = requests.post(url, data=param)
    
    status_code = response.status_code
    response = response.json()
    
    return response, status_code

def get_user_info(access_token):
    
    url = "https://api.linkedin.com/v2/userinfo"
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.get(url, headers=headers)
    
    status_code = response.status_code
    response = response.json()
    
    return response, status_code

def publish_content_linkedin(access_token, id, text):
    
    urn_id = "urn:li:person:" + id
    
    url = "https://api.linkedin.com//rest/posts"
    
    headers = {"X-Restli-Protocol-Version":"2.0.0",
               "LinkedIn-Version" : os.getenv("LINKEDIN_VERSION"),
               "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"}
    
    payload = {
    "author": urn_id,
    "commentary": text,
    "visibility": "PUBLIC",
    "distribution": {
        "feedDistribution": "MAIN_FEED",
        "targetEntities": [],
        "thirdPartyDistributionChannels": []
    },
    "lifecycleState": "PUBLISHED",
    "isReshareDisabledByAuthor": False
}
    
    response = requests.post(url, headers=headers, json=payload)
    
    return response.headers, response.status_code

    
    