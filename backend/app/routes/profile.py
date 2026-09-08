from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Application, Opportunity, Profile, SavedOpportunity, Skill
from ..schemas import ProfileIn
from .opportunities import serialize

router = APIRouter(prefix="/profile", tags=["profile"])


def csv_to_list(value: str):
    return [x.strip() for x in (value or "").split(",") if x.strip()]


@router.get("")
def get_profile(user=Depends(get_current_user), db: Session = Depends(get_db)):
    profile = user.profile
    return {
        "user_type": profile.user_type,
        "name": profile.name,
        "college": profile.college,
        "degree": profile.degree,
        "graduation_year": profile.graduation_year,
        "branch": profile.branch,
        "years_experience": profile.years_experience,
        "current_role": profile.current_role,
        "target_roles": csv_to_list(profile.target_roles),
        "preferred_locations": csv_to_list(profile.preferred_locations),
        "preferred_types": csv_to_list(profile.preferred_types),
        "preferred_tiers": csv_to_list(profile.preferred_tiers),
        "women_focused": profile.women_focused,
        "skills": [s.name for s in user.skills],
    }


@router.put("")
def update_profile(data: ProfileIn, user=Depends(get_current_user), db: Session = Depends(get_db)):
    profile = user.profile
    for field in [
        "user_type", "name", "college", "degree", "graduation_year", "branch",
        "years_experience", "current_role", "women_focused"
    ]:
        setattr(profile, field, getattr(data, field))

    profile.target_roles = ",".join(data.target_roles)
    profile.preferred_locations = ",".join(data.preferred_locations)
    profile.preferred_types = ",".join(data.preferred_types)
    profile.preferred_tiers = ",".join(data.preferred_tiers)

    user.skills.clear()
    for raw in data.skills if hasattr(data, "skills") else []:
        name = raw.strip()
        if not name:
            continue
        skill = db.query(Skill).filter(Skill.name.ilike(name)).first()
        if not skill:
            skill = Skill(name=name)
            db.add(skill)
            db.flush()
        user.skills.append(skill)

    db.commit()
    return {"message": "Profile updated"}


@router.get("/bookmarks")
def get_bookmarks(user=Depends(get_current_user), db: Session = Depends(get_db)):
    saved = (
        db.query(Opportunity)
        .join(SavedOpportunity, SavedOpportunity.opportunity_id == Opportunity.id)
        .filter(SavedOpportunity.user_id == user.id)
        .order_by(SavedOpportunity.created_at.desc())
        .all()
    )
    return [serialize(op) for op in saved]


@router.delete("/bookmarks/{opportunity_id}")
def remove_bookmark(opportunity_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    saved = (
        db.query(SavedOpportunity)
        .filter(
            SavedOpportunity.user_id == user.id,
            SavedOpportunity.opportunity_id == opportunity_id,
        )
        .first()
    )
    if saved:
        db.delete(saved)
        application = (
            db.query(Application)
            .filter(Application.user_id == user.id, Application.opportunity_id == opportunity_id, Application.status == "saved")
            .first()
        )
        if application:
            db.delete(application)
        db.commit()
    return {"removed": True}
