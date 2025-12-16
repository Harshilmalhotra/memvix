from sqlalchemy import Column, Integer, BigInteger, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base

class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    telegram_id = Column(BigInteger, nullable=False)  # 🔥 NEW

    message = Column(String, nullable=False)
    trigger_time = Column(DateTime(timezone=True), nullable=False)

    status = Column(String, default="scheduled")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
