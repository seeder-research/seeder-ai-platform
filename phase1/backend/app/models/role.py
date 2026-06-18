import enum
from sqlalchemy import Column, Integer, String, Enum as SAEnum
from app.database import Base


class RoleName(str, enum.Enum):
    admin = "admin"
    professor = "professor"
    member = "member"


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    name = Column(SAEnum(RoleName, name="user_role"), unique=True, nullable=False)
    description = Column(String)
