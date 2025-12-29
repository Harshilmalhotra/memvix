from sqlalchemy import Column, Integer, BigInteger, String, DateTime, JSON
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, index=True)
    first_name = Column(String)
    username = Column(String)
    timezone = Column(String, default="Asia/Kolkata")
    preferences = Column(JSON, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
