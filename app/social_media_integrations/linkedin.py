import os, requests
from fastapi import Depends
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.routing import APIRouter
from sqlalchemy.orm import Session
from app.models.get_db import get_db
from app.models.model import User
from app.models.social_media_integrations import LinkedIn
from app.utils.user_auth import get_current_user
from app.utils.linkedin import generate_access_token, get_user_info

router = APIRouter(tags=["linkedin"])

@router.get("/auth/linkedin/callback")
def linkedin_callback_url(code, state, db: Session = Depends(get_db)):
    
    try:
        user_id = int(state)
    except:
        return JSONResponse(content={"error": "wrong creds"}, status_code=400)

    if not code:
        return JSONResponse(content={"error": "Missing code from Linkedin"}, status_code=400)
    
    user = db.query(User).filter_by(id=user_id).first()
    
    if not user:
        return JSONResponse(content={"error": "invalid data provided"}, status_code=400)
    
    response, status_code = generate_access_token(code)
    
    if status_code != 200:
        return RedirectResponse(url=f"{os.getenv("FRONTEND_URL")}/dashboard/brain?tab=integration", status_code=302)
    
    access_token = response.get("access_token")
    
    response, status_code = get_user_info(access_token)
    
    if status_code != 200:
        return RedirectResponse(url=f"{os.getenv("FRONTEND_URL")}/dashboard/brain?tab=integration", status_code=302)

    linkedin_user_id =  response.get('sub')
    name = response.get('name')
    email = response.get('email')
    
    linkedin_user = db.query(LinkedIn).filter_by(linkedin_id=linkedin_user_id).first()
    
    if linkedin_user:
        linkedin_user.access_token = access_token
        db.commit()
        return RedirectResponse(url=f"{os.getenv("FRONTEND_URL")}/dashboard/brain?tab=integration", status_code=303)
    
    linkedin_user = LinkedIn(linkedin_id=linkedin_user_id, name=name, email=email, access_token=access_token, user_id=user_id)
    
    db.add(linkedin_user)
    db.commit()    
    return RedirectResponse(url=f"{os.getenv("FRONTEND_URL")}/dashboard/brain?tab=integration", status_code=303)
    
@router.get("/get-linkedin-accounts")
def get_connected_linkedin_accounts(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)

    accounts = db.query(LinkedIn).filter_by(user_id=user_id).all()
    account_info = []
    for account in accounts:
        linkedin_account_detail = {}
        linkedin_account_detail['name'] = account.name
        linkedin_account_detail['linkedin_id'] = account.linkedin_id
        account_info.append(linkedin_account_detail)
    return JSONResponse(content={"linkedin_account_info": account_info}, status_code=200)

@router.delete("/delete-linkedin-account/{linkedin}")
def delete_connected_linkedin_accounts(linkedin, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)

    account = db.query(LinkedIn).filter_by(linkedin_id=linkedin, user_id=user_id).first()
    if not account:
        return JSONResponse(content={"success": "Not authorized to delete the account"}, status_code=403)
    db.delete(account)
    db.commit()
    return JSONResponse(content={"success": "account deleted successfully"}, status_code=200)


