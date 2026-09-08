import os
from datetime import datetime
from urllib.request import Request, urlopen

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Interaction, Opportunity, OpportunityModeration, SourceHealth, UserReport
from ..schemas import ModerationIn, UserReportIn

router = APIRouter(tags=["governance"])


def admin_only(user):
    admins = {email.strip().lower() for email in os.getenv("ADMIN_EMAILS", "").split(",") if email.strip()}
    if user.email.lower() not in admins:
        raise HTTPException(status_code=403, detail="Admin access required")


@router.post("/opportunities/{opportunity_id}/report")
def report_opportunity(opportunity_id: int, data: UserReportIn, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not db.get(Opportunity, opportunity_id):
        raise HTTPException(status_code=404, detail="Opportunity not found")
    db.add(UserReport(user_id=user.id, opportunity_id=opportunity_id, reason=data.reason, details=data.details))
    db.commit()
    return {"reported": True}


@router.get("/admin/reports")
def list_reports(user=Depends(get_current_user), db: Session = Depends(get_db)):
    admin_only(user)
    reports = db.query(UserReport).order_by(UserReport.created_at.desc()).limit(200).all()
    return [{"id": item.id, "opportunity_id": item.opportunity_id, "reason": item.reason, "details": item.details, "status": item.status, "created_at": item.created_at} for item in reports]


@router.patch("/admin/opportunities/{opportunity_id}/moderation")
def moderate_opportunity(opportunity_id: int, data: ModerationIn, user=Depends(get_current_user), db: Session = Depends(get_db)):
    admin_only(user)
    if not db.get(Opportunity, opportunity_id):
        raise HTTPException(status_code=404, detail="Opportunity not found")
    moderation = db.query(OpportunityModeration).filter(OpportunityModeration.opportunity_id == opportunity_id).first()
    if not moderation:
        moderation = OpportunityModeration(opportunity_id=opportunity_id)
        db.add(moderation)
    moderation.status = data.status
    moderation.reason = data.reason
    moderation.reviewed_at = datetime.utcnow()
    db.commit()
    return {"updated": True}


@router.post("/admin/opportunities/{opportunity_id}/source-health")
def check_source_health(opportunity_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    admin_only(user)
    opportunity = db.get(Opportunity, opportunity_id)
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    health = opportunity.source_health or SourceHealth(opportunity_id=opportunity_id)
    try:
        request = Request(opportunity.source_url, headers={"User-Agent": "Oppora source-health/1.0"}, method="HEAD")
        with urlopen(request, timeout=8) as response:
            health.http_status = response.status
            health.check_status = "healthy" if response.status < 400 else "unhealthy"
            health.last_error = ""
    except Exception as error:
        health.check_status = "unhealthy"
        health.failure_count = (health.failure_count or 0) + 1
        health.last_error = str(error)[:500]
    health.checked_at = datetime.utcnow()
    db.add(health)
    db.commit()
    return {"status": health.check_status, "http_status": health.http_status, "failure_count": health.failure_count, "last_error": health.last_error}


@router.get("/admin/analytics")
def analytics(user=Depends(get_current_user), db: Session = Depends(get_db)):
    admin_only(user)
    event_counts = dict(db.query(Interaction.event_type, func.count(Interaction.id)).group_by(Interaction.event_type).all())
    status_counts = dict(db.query(OpportunityModeration.status, func.count(OpportunityModeration.id)).group_by(OpportunityModeration.status).all())
    source_counts = dict(db.query(SourceHealth.check_status, func.count(SourceHealth.id)).group_by(SourceHealth.check_status).all())
    return {"interactions": event_counts, "moderation": status_counts, "source_health": source_counts, "reports_open": db.query(UserReport).filter(UserReport.status == "open").count()}