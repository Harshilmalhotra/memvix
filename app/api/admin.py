from fastapi import APIRouter, Depends, BackgroundTasks, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path
from sqlalchemy import func
from datetime import datetime, timedelta

from app.core.deps import get_db
from app.models.user import User
from app.services.telegram_client import send_message

router = APIRouter(prefix="/admin", tags=["Admin"])

# Setup templates
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

@router.get("/mission-control", response_class=HTMLResponse)
def mission_control(request: Request, db: Session = Depends(get_db)):
    """Serve the Mission Control dashboard."""
    total_users = db.query(User).count()
    
    # Active users in last 24h
    one_day_ago = datetime.utcnow() - timedelta(days=1)
    active_users = db.query(User).filter(User.last_seen >= one_day_ago).count()
    
    return templates.TemplateResponse("mission_control.html", {
        "request": request,
        "total_users": total_users,
        "active_users": active_users
    })

@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """API to get latest stats."""
    total_users = db.query(User).count()
    one_day_ago = datetime.utcnow() - timedelta(days=1)
    active_users = db.query(User).filter(User.last_seen >= one_day_ago).count()
    
    return {
        "total_users": total_users,
        "active_users": active_users
    }

async def _broadcast_task(message: str, db_session_factory):
    """Background task to send broadcast messages."""
    # Create a new session for the background task
    with db_session_factory() as db:
        users = db.query(User).all()
        # In a real production app, this should be batched or queued properly (e.g. Celery/Redis)
        # to avoid hitting rate limits or timeouts.
        success_count = 0
        for user in users:
            try:
                # Basic rate limiting protection could be added here
                send_message(user.telegram_id, message)
                success_count += 1
            except Exception as e:
                print(f"Failed to send to {user.telegram_id}: {e}")
        print(f"Broadcast complete. Sent to {success_count}/{len(users)} users.")

@router.post("/broadcast")
def broadcast_message(
    payload: dict, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Broadcast a message to all users."""
    message = payload.get("message")
    if not message:
        raise HTTPException(status_code=400, detail="Message content required")
    
    # Basic security check - in prod this should be authenticated
    # For now relying on the hidden URL / internal network
    
    # We need to pass the session factory or handle session in background task
    from app.core.database import SessionLocal
    background_tasks.add_task(_broadcast_task, message, SessionLocal)
    
    return {"status": "Broadcast started"}
