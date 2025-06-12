from fastapi import HTTPException
from app.models.model import User, Team
from app.models.get_db import get_db, SessionLocal

def credit_check_appointment_settter(user_id, db = SessionLocal()):
    user = db.query(User).filter_by(id=user_id).first()
    if user:
        team = db.query(Team).filter_by(userId=user_id).first()
        if team.credits <= 19:
            return HTTPException("Insufficient balance")