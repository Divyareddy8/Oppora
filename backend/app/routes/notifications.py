from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import NotificationDelivery
from ..notifications import deadline_body, deadline_items, deliver, digest_body, digest_items, get_preferences
from ..schemas import NotificationPreferenceIn

router = APIRouter(prefix="/notifications", tags=["notifications"])


def serialize_delivery(item):
    return {"id": item.id, "channel": item.channel, "notification_type": item.notification_type,
            "subject": item.subject, "body": item.body, "status": item.status, "created_at": item.created_at}


@router.get("/preferences")
def read_preferences(user=Depends(get_current_user), db: Session = Depends(get_db)):
    preferences = get_preferences(db, user)
    db.commit()
    return {key: getattr(preferences, key) for key in ["email_enabled", "deadline_alerts", "daily_digest", "telegram_enabled", "telegram_chat_id", "digest_hour"]}


@router.put("/preferences")
def update_preferences(data: NotificationPreferenceIn, user=Depends(get_current_user), db: Session = Depends(get_db)):
    preferences = get_preferences(db, user)
    for key, value in data.model_dump().items():
        setattr(preferences, key, value)
    db.commit()
    return {"updated": True}


@router.get("/deadline-alerts")
def preview_deadline_alerts(user=Depends(get_current_user), db: Session = Depends(get_db)):
    opportunities = deadline_items(db, user)
    return {"count": len(opportunities), "opportunities": [{"id": op.id, "title": op.title, "deadline": op.deadline} for op in opportunities], "body": deadline_body(opportunities) if opportunities else "No deadlines in the next 7 days."}


@router.post("/deadline-alerts/send")
def send_deadline_alerts(user=Depends(get_current_user), db: Session = Depends(get_db)):
    preferences = get_preferences(db, user)
    opportunities = deadline_items(db, user)
    if not opportunities or not preferences.deadline_alerts:
        return {"sent": 0, "reason": "disabled" if not preferences.deadline_alerts else "no_upcoming_deadlines"}
    deliveries = deliver(db, user, "deadline_alert", "Oppora deadline alert", deadline_body(opportunities))
    return {"sent": len(deliveries), "deliveries": [serialize_delivery(item) for item in deliveries]}


@router.get("/digest")
def preview_digest(user=Depends(get_current_user), db: Session = Depends(get_db)):
    applications = digest_items(db, user)
    return {"count": len(applications), "body": digest_body(applications) if applications else "Your application tracker is empty."}


@router.post("/digest/send")
def send_digest(user=Depends(get_current_user), db: Session = Depends(get_db)):
    preferences = get_preferences(db, user)
    applications = digest_items(db, user)
    if not applications or not preferences.daily_digest:
        return {"sent": 0, "reason": "disabled" if not preferences.daily_digest else "empty_tracker"}
    deliveries = deliver(db, user, "daily_digest", "Your Oppora daily digest", digest_body(applications))
    return {"sent": len(deliveries), "deliveries": [serialize_delivery(item) for item in deliveries]}


@router.get("/history")
def notification_history(user=Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.query(NotificationDelivery).filter(NotificationDelivery.user_id == user.id).order_by(NotificationDelivery.created_at.desc()).limit(50).all()
    return [serialize_delivery(item) for item in items]