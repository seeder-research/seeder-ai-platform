from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.chat import Chat

router = APIRouter(prefix="/api/chats", tags=["chats"])


class ChatCreate(BaseModel):
    title: str = "New Chat"


@router.post("")
async def create_chat(payload: ChatCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    chat = Chat(owner_id=user.id, title=payload.title)
    db.add(chat)
    await db.commit()
    await db.refresh(chat)
    return {"id": str(chat.id), "title": chat.title}
