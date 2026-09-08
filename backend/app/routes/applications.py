from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Application, Interaction, Opportunity
from ..schemas import ApplicationIn
from .opportunities import serialize

router = APIRouter(prefix="/applications", tags=["applications"])


def serialize_application(item):
    return {
        "id": item.id,
        "status": item.status,
        "notes": item.notes,
        "applied_at": item.applied_at,
        "follow_up_date": item.follow_up_date,
        "updated_at": item.updated_at,
        "opportunity": serialize(item.opportunity),
    }


@router.get("")
def list_applications(user=Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.query(Application).filter(Application.user_id == user.id).order_by(Application.updated_at.desc()).all()
    return [serialize_application(item) for item in items]


@router.post("/{opportunity_id}")
def create_application(opportunity_id: int, data: ApplicationIn, user=Depends(get_current_user), db: Session = Depends(get_db)):
    opportunity = db.get(Opportunity, opportunity_id)
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    item = db.query(Application).filter(Application.user_id == user.id, Application.opportunity_id == opportunity_id).first()
    if not item:
        item = Application(user_id=user.id, opportunity_id=opportunity_id)
        db.add(item)
    item.status = data.status
    item.notes = data.notes
    item.applied_at = data.applied_at or (datetime.utcnow() if data.status != "saved" else None)
    item.follow_up_date = data.follow_up_date
    db.add(Interaction(user_id=user.id, opportunity_id=opportunity_id, event_type="apply" if data.status == "applied" else "view"))
    db.commit()
    db.refresh(item)
    return serialize_application(item)


@router.patch("/{application_id}")
def update_application(application_id: int, data: ApplicationIn, user=Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(Application).filter(Application.id == application_id, Application.user_id == user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Application not found")
    item.status = data.status
    item.notes = data.notes
    item.applied_at = data.applied_at or (datetime.utcnow() if data.status != "saved" else None)
    item.follow_up_date = data.follow_up_date
    db.commit()
    db.refresh(item)
    return serialize_application(item)


@router.delete("/{application_id}")
def delete_application(application_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(Application).filter(Application.id == application_id, Application.user_id == user.id).first()
    if item:
        db.delete(item)
        db.commit()
    return {"removed": True}