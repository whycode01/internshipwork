# backend/user_models.py
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from backend.base import Base  # ✅ Use shared base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
