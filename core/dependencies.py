from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db.models import User
from db.session import get_db
from core.security import decode_access_token_with_version

def get_current_user(
    token: str | None = Cookie(default=None, alias="pyyt_session"),
    db: Session = Depends(get_db),
) -> User:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please sign in.")
    decoded = decode_access_token_with_version(token)
    if not decoded:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired. Please sign in again.")
    user_id, token_version = decoded
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is unavailable.")
    if token_version != user.auth_version:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Your session was revoked. Please sign in again.")
    return user

def get_optional_user(
    token: str | None = Cookie(default=None, alias="pyyt_session"),
    db: Session = Depends(get_db),
) -> User | None:
    if not token:
        return None
    decoded = decode_access_token_with_version(token)
    if not decoded:
        return None
    user_id, token_version = decoded
    user = db.get(User, user_id)
    if not user or not user.is_active or token_version != user.auth_version:
        return None
    return user
