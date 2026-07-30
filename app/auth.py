from dataclasses import dataclass

import jwt  #to verify the token's signature 
from fastapi import HTTPException, Request, status

from app.config import JWT_ACCESS_SECRET

#Request - to access HTTP request object(like request.headers)
#HTTPException - to stop exectuion and send error (401, ...)
#status - helper module containing code (401, instead of manually)


@dataclass
class AuthContext:
    user_id: str
    role: str
    raw_token: str 
    building: str | None = None
    faculty: str | None = None
    

async def verify_jwt(request: Request) -> AuthContext: 
#async - to execute simultaneously several processes
    auth_header = request.headers.get("Authorization") #To get the value from client
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Missing or invalid Authorization header"
        ) 
    token = auth_header.split(" ")[1] #to separate token key and Bearer

    try:
        payload = jwt.decode(token, JWT_ACCESS_SECRET, algorithms = ['HS256']) #to verify identity
        auth = AuthContext(
            user_id=payload["sub"], 
            role=payload["role"], 
            building=payload.get("building"), 
            faculty=payload.get("faculty"),
            raw_token=token) #to all info from payload
        request.state.auth = auth #to store the authentication context in the request
        return auth #return the authentication context
    except jwt.ExpiredSignatureError: 
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Token has expired'
        ) from None
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        ) from None 