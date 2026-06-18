from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.deps import require_role
from app.models.user import User
from app.models.role import Role
from app.services.audit import log_action

router = APIRouter(prefix="/api/admin", tags=["admin"])


class RoleUpdateRequest(BaseModel):
    role: str  # "admin" | "professor" | "member"


class StatusUpdateRequest(BaseModel):
    is_active: bool


@router.get("/users")
async def list_users(admin: User = Depends(require_role("admin")), db: AsyncSession = Depends(get_db)):
    users = (await db.execute(select(User))).scalars().all()
    return [{"id": str(u.id), "ldap_uid": u.ldap_uid, "display_name": u.display_name,
             "email": u.email, "role": u.role.name, "is_active": u.is_active} for u in users]


@router.patch("/users/{user_id}/role")
async def update_role(user_id: str, payload: RoleUpdateRequest,
                       admin: User = Depends(require_role("admin")), db: AsyncSession = Depends(get_db)):
    role = (await db.execute(select(Role).where(Role.name == payload.role))).scalar_one_or_none()
    if not role:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid role")

    target = await db.get(User, user_id)
    if not target:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    old_role = target.role.name

    if old_role == "admin" and payload.role != "admin":
        admin_role = (await db.execute(select(Role).where(Role.name == "admin"))).scalar_one()
        remaining_admins = (await db.execute(
            select(func.count(User.id)).where(
                User.role_id == admin_role.id, User.id != target.id, User.is_active == True
            )
        )).scalar_one()
        if remaining_admins == 0:
            raise HTTPException(status.HTTP_409_CONFLICT, "Cannot demote the last remaining admin")

    target.role_id = role.id
    await db.commit()

    await log_action(db, actor_id=admin.id, action="role_change", target_type="user",
                      target_id=target.id, metadata={"from": old_role, "to": payload.role})
    return {"id": str(target.id), "role": payload.role}


@router.patch("/users/{user_id}/status")
async def update_status(user_id: str, payload: StatusUpdateRequest,
                         admin: User = Depends(require_role("admin")), db: AsyncSession = Depends(get_db)):
    target = await db.get(User, user_id)
    if not target:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    if target.role.name == "admin" and payload.is_active is False:
        admin_role = (await db.execute(select(Role).where(Role.name == "admin"))).scalar_one()
        remaining_admins = (await db.execute(
            select(func.count(User.id)).where(
                User.role_id == admin_role.id, User.id != target.id, User.is_active == True
            )
        )).scalar_one()
        if remaining_admins == 0:
            raise HTTPException(status.HTTP_409_CONFLICT, "Cannot deactivate the last remaining admin")

    old_status = target.is_active
    target.is_active = payload.is_active
    await db.commit()

    await log_action(db, actor_id=admin.id, action="status_change", target_type="user",
                      target_id=target.id, metadata={"from": old_status, "to": payload.is_active})
    return {"id": str(target.id), "is_active": target.is_active}
