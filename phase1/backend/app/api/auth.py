from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.ldap_auth import authenticate_ldap
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.core.deps import get_current_user
from app.config import settings
from app.models.user import User
from app.models.role import Role
from app.models.connector import Connector

router = APIRouter(prefix="/api/auth", tags=["auth"])

DEFAULT_CONNECTORS = [
    ("openai", "OpenAI", "https://api.openai.com/v1"),
    ("anthropic", "Anthropic", "https://api.anthropic.com/v1"),
    ("google_gemini", "Google Gemini", "https://generativelanguage.googleapis.com/v1beta"),
    ("openrouter", "OpenRouter", "https://openrouter.ai/api/v1"),
]


@router.post("/login")
async def login(response: Response, form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    ldap_info = authenticate_ldap(form.username, form.password)
    if not ldap_info:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid LDAP credentials")

    result = await db.execute(select(User).where(User.ldap_uid == ldap_info["uid"]))
    user = result.scalar_one_or_none()

    if user is None:
        # Bootstrap: only the designated cluster owner is auto-promoted to admin on first login.
        # All other new users default to "member"; admins promote via /api/admin/users/{id}/role.
        role_name = "admin" if ldap_info["uid"] == settings.bootstrap_admin_uid else "member"
        role = (await db.execute(select(Role).where(Role.name == role_name))).scalar_one()

        user = User(
            ldap_uid=ldap_info["uid"], email=ldap_info["email"],
            display_name=ldap_info["display_name"], role_id=role.id,
            uid_number=ldap_info["uid_number"], gid_number=ldap_info["gid_number"],
            home_directory=ldap_info["home_directory"],
        )
        db.add(user)
        await db.flush()  # populate user.id before creating dependent connector rows

        for provider, label, base_url in DEFAULT_CONNECTORS:
            db.add(Connector(user_id=user.id, provider=provider, label=label,
                              base_url=base_url, api_key_encrypted=None, is_seeded=True))
    else:
        # Re-sync identity attributes only — role_id is never touched here
        user.email = ldap_info["email"]
        user.display_name = ldap_info["display_name"]
        user.uid_number = ldap_info["uid_number"]
        user.gid_number = ldap_info["gid_number"]
        user.home_directory = ldap_info["home_directory"]

    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(user)

    access_token = create_access_token(str(user.id), user.role.name)
    refresh_token = create_refresh_token(str(user.id))

    response.set_cookie(key="access_token", value=access_token, httponly=True,
                         secure=True, samesite="lax", path="/", max_age=settings.jwt_expiry_seconds)
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True,
                         secure=True, samesite="lax", path="/api/auth/refresh",
                         max_age=settings.jwt_refresh_expiry_seconds)

    return {"user": {"id": str(user.id), "display_name": user.display_name,
                      "email": user.email, "role": user.role.name}}


@router.post("/refresh")
async def refresh(response: Response, request: Request, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "No refresh token")
    try:
        payload = decode_token(token)
        if payload.get("type") != "refresh":
            raise ValueError
    except Exception:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")

    user = await db.get(User, payload["sub"])
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User inactive")

    new_token = create_access_token(str(user.id), user.role.name)
    response.set_cookie(key="access_token", value=new_token, httponly=True,
                         secure=True, samesite="lax", path="/", max_age=settings.jwt_expiry_seconds)
    return {"status": "refreshed"}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/api/auth/refresh")
    return {"status": "logged_out"}


@router.get("/me")
async def me(user: User = Depends(get_current_user)):
    return {"id": str(user.id), "display_name": user.display_name,
            "email": user.email, "role": user.role.name}
