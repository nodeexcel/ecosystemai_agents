
import requests, os, uuid
from datetime import datetime, timedelta
import redis
from fastapi import Depends, Query, Request
from fastapi.routing import APIRouter
from fastapi.responses import JSONResponse, RedirectResponse

from sqlalchemy.orm import Session

from app.models.get_db import get_db
from app.models.model import User, AgentIntegrationTrack
from app.models.social_media_integrations import Tiktok
from app.schemas.social_media_integration import (FacebookCallback,
                                                InstagramMessageAlert)
from app.utils.user_auth import get_current_user
from app.utils.tiktok import user_access_token, get_user_info

router = APIRouter(tags=["Tiktok"])

@router.get("/tiktok/callback")
def tiktok_callback(request: FacebookCallback = Depends(),
                          db: Session = Depends(get_db)):
    
    code = request.code
    user_id = request.state
    user_token_info=user_access_token(code)
    access_token = user_token_info.get("access_token")
    refresh_token = user_token_info.get("refresh_token")
    expiry_time = user_token_info.get("expires_in")
    access_token_expiry_time = datetime.now() + timedelta(seconds=expiry_time)
    refresh_expiry_time = user_token_info.get("refresh_expires_in")
    refresh_token_expiry_time = datetime.now() + timedelta(seconds=refresh_expiry_time)
    
    response = get_user_info(access_token) 
    creator_username = response['data']["creator_username"]
    creator_nickname = response['data']["creator_nickname"]
    
    tiktok_user = db.query(Tiktok).filter_by(tiktok_id=user_token_info.get("open_id")).first()
    
    if tiktok_user:
        tiktok_user.access_token = access_token
        tiktok_user.refresh_token = refresh_token
        db.commit()
        return RedirectResponse(url=f"{os.getenv("FRONTEND_URL")}/dashboard/brain?tab=integration", status_code=303)
    
    tiktok_user = Tiktok(tiktok_id=user_token_info.get("open_id"), creator_nickname=creator_nickname, creator_username=creator_username,
                         access_token=access_token, refresh_token=refresh_token,access_token_expiry_time=access_token_expiry_time,
                         refresh_token_expiry_time=refresh_token_expiry_time, user_id=user_id)
    db.add(tiktok_user)
    db.commit()
    
    return RedirectResponse(url=f"{os.getenv("FRONTEND_URL")}/dashboard/brain?tab=integration", status_code=303)
  
@router.get("/get-tiktok-accounts")
def get_connected_tiktok_accounts(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)

    accounts = db.query(Tiktok).filter_by(user_id=user_id).all()
    account_info = []
    for account in accounts:
        tiktok_account_detail = {}
        tiktok_account_detail['name'] = account.creator_username
        tiktok_account_detail['nickname'] = account.creator_nickname
        tiktok_account_detail['tiktok_id'] = account.tiktok_id
        account_info.append(tiktok_account_detail)
    return JSONResponse(content={"tiktok_account_info": account_info}, status_code=200)

@router.delete("/delete-tiktok-account/{tiktok_id}")
def delete_connected_tiktok_accounts(tiktok_id, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)

    account = db.query(Tiktok).filter_by(tiktok_id=tiktok_id, user_id=user_id).first()
    if not account:
        return JSONResponse(content={"success": "Not authorized to delete the account"}, status_code=403)
    db.delete(account)
    db.commit()
    return JSONResponse(content={"success": "account deleted successfully"}, status_code=200)
  


