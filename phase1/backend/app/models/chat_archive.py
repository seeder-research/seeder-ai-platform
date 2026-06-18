import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base


class ChatArchive(Base):
    __tablename__ = "chat_archives"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_chat_id = Column(UUID(as_uuid=True), nullable=False)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(UUID(as_uuid=True), nullable=True)
    title = Column(String(255), nullable=False)
    archive_path = Column(Text, nullable=False)
    message_count = Column(Integer, nullable=False)
    original_created_at = Column(DateTime(timezone=True), nullable=False)
    original_last_activity_at = Column(DateTime(timezone=True), nullable=False)
    archived_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    archived_at = Column(DateTime(timezone=True), server_default=func.now())
    restored_at = Column(DateTime(timezone=True))
    restored_to_chat_id = Column(UUID(as_uuid=True))
    restored_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
