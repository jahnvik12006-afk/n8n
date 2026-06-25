from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.config import AUTHORIZATION_TOKEN

bearer = HTTPBearer()


def require_auth(credentials: HTTPAuthorizationCredentials = Security(bearer)):
    if credentials.credentials != AUTHORIZATION_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid authorization token")
    return credentials.credentials
