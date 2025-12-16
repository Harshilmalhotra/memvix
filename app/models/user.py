from sqlalchemy import Column, Integer, String, DateTime, BigInteger
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)


    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)

    first_name = Column(String, nullable=True)
    username = Column(String, nullable=True)
    timezone = Column(String, default="Asia/Kolkata")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
