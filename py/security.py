from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from config.settings import settings

_passwords = CryptContext(schemes=["argon2"], deprecated="auto")
ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = 30

def hash_password(password: str) -> str:
    return _passwords.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _passwords.verify(password, password_hash)
    except Exception:
        return False

def create_access_token(subject: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_MINUTES)
    return jwt.encode({"sub": subject, "exp": expires}, settings.secret_key, algorithm=ALGORITHM)

def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        subject = payload.get("sub")
        return subject if isinstance(subject, str) else None
    except JWTError:
        return None
