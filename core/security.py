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

def create_access_token(subject: str, auth_version: int = 0) -> str:
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=ACCESS_TOKEN_MINUTES)
    return jwt.encode(
        {
            "sub": subject,
            "ver": auth_version,
            "iat": now,
            "exp": expires,
        },
        settings.secret_key,
        algorithm=ALGORITHM,
    )

def decode_access_token_with_version(token: str) -> tuple[str, int] | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        subject = payload.get("sub")
        version = payload.get("ver", 0)
        if not isinstance(subject, str) or not isinstance(version, int) or isinstance(version, bool):
            return None
        return subject, version
    except JWTError:
        return None

def decode_access_token(token: str) -> str | None:
    decoded = decode_access_token_with_version(token)
    return decoded[0] if decoded else None
