import enum
import uuid
from sqlalchemy import Column, String, Text, Integer, ForeignKey, DateTime, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base


class MessageRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    parent_message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id", ondelete="SET NULL"), nullable=True)
    role = Column(SAEnum(MessageRole, name="message_role"), nullable=False)
    content = Column(Text, nullable=False)
    model_name = Column(String(100))
    input_tokens = Column(Integer)
    output_tokens = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
