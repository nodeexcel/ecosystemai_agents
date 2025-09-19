from fastapi import Request, HTTPException

def check_admin_authorization(request: Request):
    
    token = request.headers.get("authorization")
    print(token)
    if token != 'abvc':
        raise HTTPException(detail="invalid headers", status_code=403)
