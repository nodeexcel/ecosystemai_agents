import os, requests
from fastapi import HTTPException

from app.models.social_media_integrations import Tiktok

def user_access_token(code):
    url = "https://open.tiktokapis.com/v2/oauth/token/"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    params = {"client_key": os.getenv("TIKTOK_CLIENT_ID"),
              "client_secret": os.getenv("TIKTOK_CLIENT_SECRET"),
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": os.getenv("TIKTOK_REDIRECT_URI")}
    response = requests.post(url, headers=headers, data=params)
    if response.status_code!=200:
        raise HTTPException(detail="Something went wrong", status_code=500)
    user_token_info = response.json()
    return user_token_info

def get_user_info(access_token):
    
    url = "https://open.tiktokapis.com/v2/post/publish/creator_info/query/"
    header = {"Authorization": f"Bearer {access_token}",
              "Content-Type": "application/json; charset=UTF-8"
              }
    response = requests.post(url, headers=header)
    
    if response.status_code!=200:
        raise HTTPException(detail="Something went wrong", status_code=500)
    response = response.json() 
    return response

def get_refresh_access_token(refresh_token):
    url = "https://open.tiktokapis.com/v2/oauth/token/"

    header = {"Content-Type": "application/x-www-form-urlencoded",
            "Cache-Control": "no-cache" }
    data = {"client_key": os.getenv("TIKTOK_CLIENT_ID"),
            "client_secret": os.getenv("TIKTOK_CLIENT_SECRET"),
            "grant_type": "refresh_token",
            "refresh_token": refresh_token}
    response = requests.post(url, headers=header, data=data)
    response = response.json()
    access_token = response.get("access_token")
    if not access_token:
        raise HTTPException(detail="Please reverify your tiktok account", status_code=500)
    return access_token, response

def post_on_tiktok(access_token, refresh_token, media_url, text):
    
    url = "https://open.tiktokapis.com//v2/post/publish/video/init/"
    
    header = {"Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json; charset=UTF-8"
                }
    
    refresh_token_response = None
    
    payload = {"post_info": {
        "title": text,
        "privacy_level": "SELF_ONLY",
        "disable_duet": False,
        "disable_comment": False,
        "disable_stitch": False,
        "video_cover_timestamp_ms": 1000
    },
    "source_info": {
        "source": "PULL_FROM_URL",
        "video_url": media_url
    }}
    response = requests.post(url, headers=header, json=payload)
    if response.status_code != 200:
        access_token, refresh_token_response = get_refresh_access_token(refresh_token)
        url = "https://open.tiktokapis.com//v2/post/publish/video/init/"
    
        header = {"Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json; charset=UTF-8"
                    }
        
        payload = {"post_info": {
            "title": text,
            "privacy_level": "SELF_ONLY",
            "disable_duet": False,
            "disable_comment": False,
            "disable_stitch": False,
            "video_cover_timestamp_ms": 1000
        },
        "source_info": {
            "source": "PULL_FROM_URL",
            "video_url": media_url
        }}
        response = requests.post(url, headers=header, json=payload)
        if response.status_code != 200:
            raise HTTPException(detail="Problem with the posting content. Please try with different video or after sometime", status_code=500)
    response = response.json()
    publish_id = response["data"]["publish_id"]
    return publish_id, refresh_token_response