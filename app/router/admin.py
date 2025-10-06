import uuid
from datetime import date, datetime, timedelta, timezone
from fastapi import Depends
from fastapi.routing import APIRouter
from fastapi.responses import JSONResponse 

from sqlalchemy.orm import Session
from app.models.get_db import get_db
from app.models.model import User, KnowledgeBase, Team, TeamMember
from app.models.phone_agent import CallRecord
from app.models.appointment_setter import AppointmentSetter
from app.models.phone_agent import PhoneAgent
from app.utils.admin import check_admin_authorization
from app.schemas.admin import CreateUser, SubscriptionUpdate, CreditRequest

router = APIRouter(tags=["admin"])

@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), verify = Depends(check_admin_authorization)):
    
    user_count = db.query(User).filter_by(isDeleted=False).count()
    call_records = db.query(CallRecord).count()
    appointment_agents = db.query(AppointmentSetter).filter_by(is_active=True).count()
    phone_agents = db.query(PhoneAgent).filter_by(status=True).count()
    total_active_agents = appointment_agents + phone_agents
    user_deleted = db.query(User).filter_by(isDeleted=True).count()
    
    response = {
        "total_users": user_count,
        "total_active_agents": total_active_agents,
        "calls": call_records,
        "phone_agents": phone_agents,
        "appointment_agents": appointment_agents,
        "user_deletd": user_deleted,        
}
    
    return JSONResponse(content={"success": response}, status_code=200)
    
    
@router.get("/user-management")
def user_management(db: Session = Depends(get_db), verify = Depends(check_admin_authorization)):
    
    users = db.query(User).filter_by(isDeleted=False).all()
    
    response = []
    
    for user in users:
        user_info = {}
        
        user_info['id'] = user.id
        try:
            user_info['name'] = user.firstName + user.lastName
        except:
            user_info['name'] = ""
        user_info['email'] = user.email
        user_info['business_name'] = user.company
        try:
            user_info['location'] = user.city + user.country
        except:
            user_info['location'] = ""
        user_info["subscriptionType"] = user.subscriptionType,
        user_info["subscriptionStatus"] = user.subscriptionStatus,
        user_info["subscriptionStartDate"] = str(user.subscriptionStartDate) if user.subscriptionStartDate else None,
        user_info["subscriptionEndDate"] = str(user.subscriptionEndDate) if user.subscriptionEndDate else None,
        user_info["subscriptionDurationType"] = user.subscriptionDurationType,
        user_info["subscriptionUpdatedAt"] = str(user.subscriptionUpdatedAt) if user.subscriptionUpdatedAt else None,
        response.append(user_info)
        
        
    return JSONResponse(content={'success': response}, status_code=200)


@router.delete("/delete-user/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), verify = Depends(check_admin_authorization)):
    
    user = db.query(User).filter_by(id=user_id).first()
    
    if not user:
        return JSONResponse(content={'success': "user cannot get deleted"}, status_code=404)
    
    
    user.isDeleted = True
    db.commit()
    
    return JSONResponse(content={'success': "user deleted successfullly"}, status_code=200)

@router.get("/get-users-knowledges")
def users_knowledge_bases(db: Session = Depends(get_db), verify = Depends(check_admin_authorization)):
    
    knowledge_bases = db.query(KnowledgeBase).all()
    
    knowledge_base_info = {}
    
    for knowledge_base in knowledge_bases:
        
        if knowledge_base.user_id in knowledge_base_info:
            knowledge_base_info[knowledge_base.user_id][knowledge_base.data_type] = knowledge_base_info[knowledge_base.user_id][knowledge_base.data_type] + 1
            
        if knowledge_base.user_id not in knowledge_base_info:
            knowledge_base_info[knowledge_base.user_id] = {
                'snippet': 0,
                'website': 0,
                'files': 0,
            }
            
            knowledge_base_info[knowledge_base.user_id][knowledge_base.data_type] = knowledge_base_info[knowledge_base.user_id][knowledge_base.data_type] + 1
            
    return JSONResponse(content={'success': knowledge_base_info}, status_code=200)
            
@router.get("/get-user-knowledge/{user_id}")
def users_knowledge_bases(user_id: int, db: Session = Depends(get_db), verify = Depends(check_admin_authorization)):
    
    knowledge_bases = db.query(KnowledgeBase).filter_by(user_id=user_id).all()
    
    response = []
    
    for knowledge_base in knowledge_bases:
        
        knowledge_base_info = {}
        
        knowledge_base_info['id'] = knowledge_base.id
        knowledge_base_info['name'] = knowledge_base.data
        knowledge_base_info['type'] = knowledge_base.data_type
        knowledge_base_info['path'] = knowledge_base.path
        knowledge_base_info['created'] = knowledge_base.created_at
        response.append(knowledge_base_info)
        
        return JSONResponse(content={'success': response}, status_code=200)
    
@router.delete("/delete-user-knowledge_base/{user_id}")
def delete_user_knowledge_base(user_id: int, db: Session = Depends(get_db),
                               verify = Depends(check_admin_authorization)):
    
    db.query(KnowledgeBase).filter_by(user_id=user_id).delete()
    
    return JSONResponse(content={'success': "Knowledge_base for user deleted successfully"}, status_code=200)

@router.delete("/delete-knowledge_base/{knowledge_base_id}")
def delete_knowledge_base(knowledge_base_id: int, db: Session = Depends(get_db)):
    
    knowledge_base = db.query(KnowledgeBase).filter_by(id=knowledge_base_id).first()
    
    if not knowledge_base:
        return JSONResponse(content={'success': "Knowledge_base cannot get deleted"}, status_code=200)
    
    db.delete(knowledge_base)
    
    return JSONResponse(content={'success': "Knowledge_base deleted successfully"}, status_code=200)

@router.post("/add-user")
def create_user(user: CreateUser, db: Session = Depends(get_db), 
                verify = Depends(check_admin_authorization)):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        return JSONResponse(content={"detail":"Email already registered"}, status_code=400)

    start_date = datetime.now(timezone.utc)

    if user.subscriptionType.lower() == "pro":
        end_date = start_date + timedelta(days=30)
        number_of_renew_months = 1
    elif user.subscriptionType.lower() == "team":
        end_date = start_date + timedelta(days=365)
        number_of_renew_months = 12
    else:
        return JSONResponse(content={"detail":"Invalid subscription type"}, status_code=400)

    new_user = User(
        email=user.email,
        role=user.role,
        subscriptionType=user.subscriptionType,
        subscriptionStatus="active",
        isDeleted=False,
        subscriptionDurationType=user.subscriptionDurationType,
        subscriptionStartDate=start_date,
        subscriptionEndDate=end_date,
        subscriptionUpdatedAt=datetime.now(timezone.utc)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    team_id = str(uuid.uuid4())
    today_date = start_date.date()
    team = Team(
        id=team_id,
        userId=new_user.id,
        numberOfTeamMembers=1,
        creditRenewDate=today_date,
        numberOfRenewMonths=number_of_renew_months,
        nextMonthRenewDate=(today_date + timedelta(days=30 * number_of_renew_months)),
        credits=0
    )
    db.add(team)
    db.commit()
    db.refresh(team)

    team_member = TeamMember(
        isAdmin=True,
        role=new_user.role,
        teamId=team.id,
        userId=new_user.id,
    )
    db.add(team_member)
    db.commit()
    db.refresh(team_member)

    return JSONResponse(content={
        "id": new_user.id,
        "email": new_user.email,
        "subscriptionType": new_user.subscriptionType,
        "subscriptionStartDate": str(new_user.subscriptionStartDate),
        "subscriptionEndDate": str(new_user.subscriptionEndDate)
    }, status_code=201)
    
@router.put("/users/{user_id}/subscription")
def update_subscription(user_id: int, payload: SubscriptionUpdate, db: Session = Depends(get_db),
                        verify = Depends(check_admin_authorization)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return JSONResponse(content={"detail":"User not found"}, status_code=404)

    today = date.today()

    if payload.subscriptionType.lower() == "pro":
        if payload.subscriptionDurationType == "monthly":
            end_date = today + timedelta(days=30)
            duration_type = "monthly"
            renew_months = 0
        if payload.subscriptionDurationType == "yearly":
            end_date = today + timedelta(days=365)
            duration_type = "yearly"
            renew_months = 11
    elif payload.subscriptionType.lower() == "team":
        if payload.subscriptionDurationType == "monthly":
            end_date = today + timedelta(days=30)
            duration_type = "monthly"
            renew_months = 0
        if payload.subscriptionDurationType == "yearly":
            end_date = today + timedelta(days=365)
            duration_type = "yearly"
            renew_months = 11
    else:
        return JSONResponse(content={"detail":"Invalid subscription type"}, status_code=400)

    user.subscriptionType = payload.subscriptionType
    user.subscriptionStatus = payload.subscriptionStatus
    user.subscriptionStartDate = today
    user.subscriptionEndDate = end_date
    user.subscriptionDurationType = duration_type
    user.subscriptionUpdatedAt = datetime.now(timezone.utc)

    team = db.query(Team).filter(Team.userId == user.id).first()
    if team:
        team.creditRenewDate = today
        team.nextMonthRenewDate = today + timedelta(days=30)
        team.numberOfRenewMonths = renew_months

    db.commit()
    db.refresh(user)

    return JSONResponse(content={
        "user_id": user.id,
        "subscriptionType": user.subscriptionType,
        "subscriptionStatus": user.subscriptionStatus,
        "subscriptionStartDate": str(user.subscriptionStartDate),
        "subscriptionEndDate": str(user.subscriptionEndDate),
        "subscriptionDurationType": user.subscriptionDurationType,
        }, status_code=200
    )
    
@router.get("/users/{user_id}")
def get_user_by_id(user_id: int, db: Session = Depends(get_db),
                   verify = Depends(check_admin_authorization)):
    user = db.query(User).filter(User.id == user_id, User.isDeleted == False).first()
    if not user:
        return JSONResponse(content={"detail":"User not found"}, status_code=404)   
    return JSONResponse(
        content={"id": user.id,
        "email": user.email,
        "role": user.role,
        "subscriptionType": user.subscriptionType,
        "subscriptionStatus": user.subscriptionStatus,
        "subscriptionStartDate": str(user.subscriptionStartDate) if user.subscriptionStartDate else None,
        "subscriptionEndDate": str(user.subscriptionEndDate) if user.subscriptionEndDate else None,
        "subscriptionDurationType": user.subscriptionDurationType,
        "subscriptionUpdatedAt": str(user.subscriptionUpdatedAt) if user.subscriptionUpdatedAt else None,}
    )
    

@router.post("/users/{user_id}/add-credits")
def add_credits(user_id: int, payload: CreditRequest, db: Session = Depends(get_db),
                verify = Depends(check_admin_authorization)):
    team = db.query(Team).filter(Team.userId == user_id).first()
    if not team:
        return JSONResponse(status_code=404, content={"detail":"Team not found for this user"})

    if payload.credits <= 0:
        return JSONResponse(status_code=400, detail="Credits must be greater than 0")

    team.credits += payload.credits
    db.commit()
    db.refresh(team)

    return JSONResponse(
        content={"userId": user_id,
        "teamId": team.id,
        "newCredits": team.credits}, status_code=200
    )
            
            
            
            
    
        
    
    
    
    
    