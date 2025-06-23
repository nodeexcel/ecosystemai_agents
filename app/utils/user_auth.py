import os
from fastapi import Depends, HTTPException, WebSocket
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

SECRET_KEY = os.getenv('JWT_SECRET')
ALGORITHM = "HS256"

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="fake")

def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload.get("userId")


async def get_user_id_from_websocket(websocket: WebSocket, token) -> str:    
    if not token:
        await websocket.close(code=1008)
        raise Exception("Missing authentication token")

    payload = verify_token(token)
    if not payload or "userId" not in payload:
        await websocket.close(code=1008)
        raise Exception("Invalid or expired token")

    return payload["userId"]