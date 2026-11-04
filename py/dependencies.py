from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db.models import User
from db.session import get_db
from py.security import decode_access_token

def get_current_user(
    token: str | None = Cookie(default=None, alias="pyyt_session"),
    db: Session = Depends(get_db),
) -> User:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please sign in.")
    user_id = decode_access_token(token)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired. Please sign in again.")
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is unavailable.")
    return user
