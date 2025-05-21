from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from database import Base
from .user import User

class ChatLog(Base):
    __tablename__ = "chat_logs"
    __table_args__ = {'extend_existing': True}



    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), nullable=False)
    role = Column(String(10), nullable=False)  # 'user' or 'bot'
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = {'extend_existing': True}

    session_id   = Column(Integer, primary_key=True, index=True, autoincrement=True)  # ← single PK
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    message   = Column(Text, nullable=False)
    answer     = Column(JSON, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

