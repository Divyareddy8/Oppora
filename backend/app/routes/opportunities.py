from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..matching import (
    inferred_company_tier,
    matching_skills,
    opportunity_fingerprint,
    semantic_similarity,
)
from ..models import Opportunity, SavedOpportunity, Skill

router = APIRouter(prefix="/opportunities", tags=["opportunities"])


def csv(value):
    return {x.strip().lower() for x in (value or "").split(",") if x.strip()}


def score_opportunity(op, profile, user):
    score = 0
    reasons = []

    target_roles = csv(profile.target_roles)
    preferred_locations = csv(profile.preferred_locations)
    preferred_types = csv(profile.preferred_types)
    preferred_tiers = csv(profile.preferred_tiers)
    company_tier = inferred_company_tier(op)
    overlap = matching_skills(user, op)

    if target_roles and any(
        r in op.role.lower() or op.role.lower() in r for r in target_roles
    ):
        score += 30
        reasons.append("Your target role matches")

    if overlap:
        score += min(25, 5 * len(overlap))
        reasons.append(f"Skill overlap: {', '.join(overlap)}")

    semantic_score = semantic_similarity(profile, user, op)
    if semantic_score >= 0.2:
        score += round(semantic_score * 30)
        reasons.append(f"Semantic match: {round(semantic_score * 100)}% based on your profile")

    if preferred_locations and (
        op.location.lower() in preferred_locations or "remote" in preferred_locations
        and "remote" in op.location.lower()
    ):
        score += 15
        reasons.append("Location preference matches")

    if preferred_types and op.opportunity_type.lower() in preferred_types:
        score += 10
        reasons.append("Opportunity type matches")

    if preferred_tiers and company_tier.lower() in preferred_tiers:
        score += 10
        reasons.append(f"{company_tier}-tier preference matches")

    if op.verified:
        score += 5
        reasons.append("Verified source")

    if op.deadline:
        days = (op.deadline - date.today()).days
        if 0 <= days <= 7:
            score += 5
            reasons.append("Deadline is within 7 days")

    if profile.women_focused and op.women_focused:
        score += 5
        reasons.append("Matches women-focused preference")

    return min(score, 100), reasons, round(semantic_score * 100)


def serialize(op, score=None, reasons=None, semantic_score=None):
    return {
        "id": op.id,
        "title": op.title,
        "organization": op.organization,
        "opportunity_type": op.opportunity_type,
        "role": op.role,
        "description": op.description,
        "source_url": op.source_url,
        "source_name": op.source_name,
        "deadline": op.deadline,
        "location": op.location,
        "experience_min": op.experience_min,
        "experience_max": op.experience_max,
        "company_tier": op.company_tier,
        "inferred_company_tier": inferred_company_tier(op),
        "verified": op.verified,
        "women_focused": op.women_focused,
        "skills": [s.name for s in op.skills],
        "match_score": score,
        "semantic_score": semantic_score,
        "reasons": reasons or [],
    }


@router.get("")
def list_opportunities(
    search: str = "",
    opportunity_type: str = "",
    role: str = "",
    location: str = "",
    tier: str = "",
    verified_only: bool = False,
    db: Session = Depends(get_db),
):
    q = db.query(Opportunity)

    if search:
        like = f"%{search}%"
        q = q.filter(
            Opportunity.title.ilike(like)
            | Opportunity.organization.ilike(like)
            | Opportunity.description.ilike(like)
            | Opportunity.role.ilike(like)
        )
    if opportunity_type:
        q = q.filter(Opportunity.opportunity_type.ilike(opportunity_type))
    if role:
        q = q.filter(Opportunity.role.ilike(f"%{role}%"))
    if location:
        q = q.filter(Opportunity.location.ilike(f"%{location}%"))
    if tier:
        q = q.filter(Opportunity.company_tier == tier)
    if verified_only:
        q = q.filter(Opportunity.verified == True)

    return [serialize(op) for op in q.order_by(Opportunity.deadline.asc()).all()]


@router.get("/feed")
def personalized_feed(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    profile = user.profile
    opportunities = db.query(Opportunity).all()

    ranked = []
    seen = set()
    for op in opportunities:
        fingerprint = opportunity_fingerprint(op)
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        score, reasons, semantic_score = score_opportunity(op, profile, user)
        ranked.append((score, op.deadline or date.max, op, reasons, semantic_score))

    ranked.sort(key=lambda x: (-x[0], x[1]))
    return [serialize(op, score, reasons, semantic_score) for score, _, op, reasons, semantic_score in ranked]


@router.get("/{opportunity_id}")
def get_opportunity(opportunity_id: int, db: Session = Depends(get_db)):
    op = db.get(Opportunity, opportunity_id)
    if not op:
        return {"detail": "Opportunity not found"}
    return serialize(op)


@router.post("/{opportunity_id}/save")
def save_opportunity(opportunity_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if not db.get(Opportunity, opportunity_id):
        return {"detail": "Opportunity not found"}

    existing = (
        db.query(SavedOpportunity)
        .filter(
            SavedOpportunity.user_id == user.id,
            SavedOpportunity.opportunity_id == opportunity_id,
        )
        .first()
    )
    if not existing:
        db.add(SavedOpportunity(user_id=user.id, opportunity_id=opportunity_id))
        db.commit()

    return {"saved": True}
