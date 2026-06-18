from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.deps import get_current_user
from app.core.crypto import encrypt_api_key, decrypt_api_key
from app.models.user import User
from app.models.connector import Connector
from app.schemas.connector import ConnectorCreate, ConnectorUpdate, ConnectorOut

router = APIRouter(prefix="/api/connectors", tags=["connectors"])


def _to_out(c: Connector) -> ConnectorOut:
    preview = None
    if c.api_key_encrypted:
        try:
            key = decrypt_api_key(c.api_key_encrypted)
            preview = f"...{key[-4:]}" if len(key) >= 4 else "...."
        except Exception:
            preview = None
    return ConnectorOut(id=c.id, provider=c.provider, label=c.label, base_url=c.base_url,
                         is_configured=c.api_key_encrypted is not None, key_preview=preview,
                         is_seeded=c.is_seeded, is_active=c.is_active, updated_at=c.updated_at)


@router.get("", response_model=list[ConnectorOut])
async def list_connectors(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    result = await db.execute(select(Connector).where(Connector.user_id == user.id).order_by(Connector.created_at))
    return [_to_out(c) for c in result.scalars().all()]


@router.post("", response_model=ConnectorOut, status_code=status.HTTP_201_CREATED)
async def create_connector(payload: ConnectorCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Always created as a custom, non-seeded row — multiple per user are allowed,
    # each with its own user-chosen label.
    connector = Connector(user_id=user.id, provider=payload.provider, label=payload.label,
                           base_url=payload.base_url, api_key_encrypted=encrypt_api_key(payload.api_key),
                           is_seeded=False)
    db.add(connector)
    await db.commit()
    await db.refresh(connector)
    return _to_out(connector)


@router.patch("/{connector_id}", response_model=ConnectorOut)
async def update_connector(connector_id: str, payload: ConnectorUpdate,
                            user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    connector = await db.get(Connector, connector_id)
    if not connector or connector.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Connector not found")

    if connector.is_seeded:
        # Identity fields (label/base_url/provider) are locked for the 4 defaults.
        # Only the API key (and active toggle) may be set — otherwise the seeded
        # rows would be unusable, since users must supply their own key.
        if payload.label is not None or payload.base_url is not None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                 "Default connectors are locked — only the API key can be set")
        if payload.api_key is not None:
            connector.api_key_encrypted = encrypt_api_key(payload.api_key)
        if payload.is_active is not None:
            connector.is_active = payload.is_active
    else:
        if payload.label is not None:
            connector.label = payload.label
        if payload.base_url is not None:
            connector.base_url = payload.base_url
        if payload.api_key is not None:
            connector.api_key_encrypted = encrypt_api_key(payload.api_key)
        if payload.is_active is not None:
            connector.is_active = payload.is_active

    await db.commit()
    await db.refresh(connector)
    return _to_out(connector)


@router.delete("/{connector_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connector(connector_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    connector = await db.get(Connector, connector_id)
    if not connector or connector.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Connector not found")
    if connector.is_seeded:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Default connectors cannot be deleted")

    await db.delete(connector)
    await db.commit()
