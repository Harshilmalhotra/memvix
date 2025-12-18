from app.core.database import Base
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, ForeignKey
from sqlalchemy.sql import func
import uuid

class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)

    public_id = Column(
        String,
        unique=True,
        index=True,
        default=lambda: uuid.uuid4().hex[:8]
    )

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    telegram_id = Column(BigInteger, nullable=False)

    message = Column(String, nullable=False)
    trigger_time = Column(DateTime(timezone=True), nullable=False)

    timezone = Column(String, default="UTC")  # 🔥 ADD THIS

    status = Column(String, default="scheduled")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
