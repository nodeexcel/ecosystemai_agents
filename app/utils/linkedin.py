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

def publish_content_linkedin(access_token, id, text, media_type, media_url=None):
    
    urn_id = "urn:li:person:" + id
    
    headers = {"X-Restli-Protocol-Version":"2.0.0",
                "LinkedIn-Version" : os.getenv("LINKEDIN_VERSION"),
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"}
    
    if media_type == "text":
        
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
        
    if media_type == "image":
        
        url = "https://api.linkedin.com/rest/images?action=initializeUpload"

        data = {
        "initializeUploadRequest": {
                "owner": urn_id
        }}
        
        response = requests.post(url, headers=headers, json=data)
        
        response = response.json()
        
        linkedin_upload_url = response['value']['uploadUrl']
        linkedin_media_id = response['value']['image']
        
        image_content = requests.get(media_url).content
        
        headers = {"X-Restli-Protocol-Version":"2.0.0",
                "LinkedIn-Version" : os.getenv("LINKEDIN_VERSION"),
                "Authorization": f"Bearer {access_token}"}
        
        response = requests.put(linkedin_upload_url, headers=headers, data=image_content)
        
        if response.status_code == 201:
            payload = {
            "author": urn_id,
            "commentary": text,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": []
            },
            "content": {
            "media": {
            "title":"title of the image",
            "id": linkedin_media_id
            }},
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False
        }
            
    if media_type == "document":
        
        url = "https://api.linkedin.com/rest/documents?action=initializeUpload"

        data = {
        "initializeUploadRequest": {
                "owner": urn_id
        }}
        
        response = requests.post(url, headers=headers, json=data)
        
        response = response.json()
        
        linkedin_upload_url = response['value']['uploadUrl']
        linkedin_media_id = response['value']['document']
        
        document_content = requests.get(media_url, stream=True)
        
        headers = {"X-Restli-Protocol-Version":"2.0.0",
                "LinkedIn-Version" : os.getenv("LINKEDIN_VERSION"),
                "Authorization": f"Bearer {access_token}"}
        
        response = requests.put(linkedin_upload_url, headers=headers, data=document_content.raw)

        if response.status_code == 201:
            payload = {
            "author": urn_id,
            "commentary": text,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": []
            },
            "content": {
            "media": {
            "title":"title of the image",
            "id": linkedin_media_id
            }},
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False
        }
        
    if media_type == "video":
        url = "https://api.linkedin.com/rest/videos?action=initializeUpload"

        data = {
        "initializeUploadRequest": {
                "owner": urn_id,
                "fileSizeBytes": 1055736,
                "uploadCaptions": False,
                "uploadThumbnail": False
        }}
        response = requests.post(url, headers=headers, json=data)

        response = response.json()
        
        upload_instructions = response['value']['uploadInstructions']
        linkedin_media_id = response['value']['video']
        
        for upload_instruction in upload_instructions:
            linkedin_upload_url = upload_instruction.get('uploadUrl')
            
        video_content = requests.get(media_url, stream=True)
        
        headers = {"X-Restli-Protocol-Version":"2.0.0",
                "LinkedIn-Version" : os.getenv("LINKEDIN_VERSION"),
                "Authorization": f"Bearer {access_token}"}
        
        response = requests.put(linkedin_upload_url, headers=headers, data=video_content.raw)

        if response.status_code == 200:
            payload = {
            "author": urn_id,
            "commentary": text,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": []
            },
            "content": {
            "media": {
            "title":"title of the image",
            "id": linkedin_media_id
            }},
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False
        }
            
    url = "https://api.linkedin.com//rest/posts"
        
    response = requests.post(url, headers=headers, json=payload)
    
    return response.headers, response.status_code

    
    