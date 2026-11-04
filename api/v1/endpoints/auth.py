import secrets
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from config.settings import settings
from db.models import Channel, User
from db.schemas import LoginRequest, RegisterRequest, UserResponse
from db.session import get_db
from py.dependencies import get_current_user
from py.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth")

def _set_session(response: Response, user: User) -> None:
    token = create_access_token(user.id)
    csrf = secrets.token_urlsafe(32)
    common = {
        "secure": settings.session_cookie_secure,
        "samesite": settings.session_cookie_samesite,
        "path": "/",
    }
    response.set_cookie("pyyt_session", token, httponly=True, max_age=1800, **common)
    response.set_cookie("pyyt_csrf", csrf, httponly=False, max_age=1800, **common)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    existing = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    user = User(
        email=payload.email.lower(),
        display_name=payload.display_name.strip(),
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.flush()
    handle_base = "".join(ch.lower() if ch.isalnum() else "-" for ch in payload.display_name).strip("-")[:28] or "creator"
    handle = f"{handle_base}-{user.id[:6]}"
    db.add(Channel(owner_id=user.id, handle=handle, name=payload.display_name.strip()))
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Could not create this account. Please try again.")
    _set_session(response, user)
    return user

@router.post("/login", response_model=UserResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Email or password is incorrect.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="This account is disabled.")
    _set_session(response, user)
    return user

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response):
    response.delete_cookie("pyyt_session", path="/")
    response.delete_cookie("pyyt_csrf", path="/")
    response.status_code = status.HTTP_204_NO_CONTENT

@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return user
