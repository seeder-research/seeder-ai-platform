from datetime import datetime, timedelta, timezone
import jwt
from app.config import settings


def create_access_token(user_id: str, role: str) -> str:
    payload = {
        "sub": user_id, "role": role, "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(seconds=settings.jwt_expiry_seconds),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: str) -> str:
    payload = {
        "sub": user_id, "type": "refresh",
        "exp": datetime.now(timezone.utc) + timedelta(seconds=settings.jwt_refresh_expiry_seconds),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
