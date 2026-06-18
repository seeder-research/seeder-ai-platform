# Importing every model module here ensures they all register with the shared
# SQLAlchemy `Base.metadata` at startup — not just whichever ones happen to be
# imported by an API router that's currently in use. Without this, models with
# no endpoint referencing them yet (e.g. Branch, ChatArchive) never get loaded,
# and any OTHER model with a foreign key pointing at their table will fail with
# `NoReferencedTableError` the first time SQLAlchemy tries to flush.
from app.models.role import Role
from app.models.user import User
from app.models.chat import Chat
from app.models.message import Message
from app.models.branch import Branch
from app.models.chat_archive import ChatArchive
from app.models.audit_log import AuditLog
from app.models.connector import Connector

__all__ = [
    "Role", "User", "Chat", "Message", "Branch",
    "ChatArchive", "AuditLog", "Connector",
]
