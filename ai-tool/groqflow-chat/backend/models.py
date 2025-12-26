from datetime import datetime

from sqlalchemy import (Column, DateTime, ForeignKey, Integer, LargeBinary,
                        String, Text)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)
    title = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String)
    type = Column(String)
    content = Column(Text, nullable=True)
    image = Column(LargeBinary, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
