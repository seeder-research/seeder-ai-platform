from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class ConnectorCreate(BaseModel):
    provider: str = "custom"
    label: str
    base_url: str
    api_key: str


class ConnectorUpdate(BaseModel):
    label: str | None = None
    base_url: str | None = None
    api_key: str | None = None     # if provided, re-encrypts
    is_active: bool | None = None


class ConnectorOut(BaseModel):
    id: UUID
    provider: str
    label: str
    base_url: str
    is_configured: bool
    key_preview: str | None        # e.g. "...ab12" — never the full key
    is_seeded: bool
    is_active: bool
    updated_at: datetime
