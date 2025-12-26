from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.base import Base  # ✅ Shared declarative base
from backend.user_models import User  # ✅ Ensures 'users' table is registered

USER_DB_URL = "sqlite:///./user.db"
user_engine = create_engine(USER_DB_URL, connect_args={"check_same_thread": False})
UserSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=user_engine)

def create_user_table():
    Base.metadata.create_all(bind=user_engine)
