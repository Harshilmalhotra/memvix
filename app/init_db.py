from app.core.database import engine, Base
from app.models.user import User
from app.models.reminder import Reminder

Base.metadata.create_all(bind=engine)
