from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..company_catalog import COMPANY_DIRECTORY
from ..database import get_db
from ..matching import (
    _sentence_model,
    build_interaction_matrix,
    candidate_generation,
    inferred_company_tier,
    matching_skills,
    ndcg_at_k,
    opportunity_fingerprint,
    precision_at_k,
    rank_candidates,
    recall_at_k,
    semantic_similarity,
)
from ..models import Application, Interaction, Opportunity, SavedOpportunity, Skill
from ..models import RecommendationPreference
from ..schemas import InteractionIn, RecommendationPreferenceIn

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


def seniority_score(op, profile, preference):
    experience = profile.years_experience or 0
    target = (preference.target_seniority if preference else "auto")
    if target == "auto":
        target = "intern" if experience == 0 else "junior" if experience <= 2 else "mid" if experience <= 5 else "senior"
    ranges = {"intern": (0, 1), "junior": (0, 3), "mid": (2, 6), "senior": (5, 20), "lead": (8, 30)}
    minimum, maximum = ranges.get(target, (0, 30))
    opportunity_min = op.experience_min or 0
    opportunity_max = op.experience_max or max(opportunity_min, 30)
    return 1.0 if opportunity_max >= minimum and opportunity_min <= maximum else 0.0


def serialize(op, score=None, reasons=None, semantic_score=None, recommendation=None):
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
        "rank_score": recommendation.get("rank_score") if recommendation else None,
        "candidate_sources": recommendation.get("candidate_sources", []) if recommendation else [],
        "interaction_score": recommendation.get("interaction_score", 0) if recommendation else 0,
        "cold_start": recommendation.get("cold_start", False) if recommendation else False,
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
    preference = user.recommendation_preferences
    opportunities = db.query(Opportunity).all()
    interactions = db.query(Interaction).all()
    candidates = candidate_generation(profile, user, opportunities, interactions, preference)
    ranked = rank_candidates(candidates, lambda op: score_opportunity(op, profile, user))
    seen = set()
    results = []
    cold_start = not any(item.user_id == user.id and item.event_type in {"view", "save", "apply"} for item in interactions)
    for recommendation in ranked:
        op = recommendation["opportunity"]
        fingerprint = opportunity_fingerprint(op)
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        results.append(serialize(
            op,
            recommendation["rank_score"],
            recommendation["reasons"],
            recommendation["semantic_score"],
            {**recommendation, "cold_start": cold_start},
        ))
    return results


@router.get("/companies")
def company_directory(tier: str = ""):
    companies = list(COMPANY_DIRECTORY.values())
    if tier:
        companies = [company for company in companies if company["tier"].lower() == tier.lower()]
    return sorted(companies, key=lambda company: (company["tier"], company["name"].lower()))


@router.get("/recommendation-diagnostics")
def recommendation_diagnostics(
    k: int = 5,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    profile = user.profile
    preference = user.recommendation_preferences
    opportunities = db.query(Opportunity).all()
    interactions = db.query(Interaction).all()
    matrix = build_interaction_matrix(interactions)
    ranked = rank_candidates(
        candidate_generation(profile, user, opportunities, interactions, preference),
        lambda op: score_opportunity(op, profile, user),
    )
    recommended_ids = [item["opportunity"].id for item in ranked]
    relevant_ids = {item_id for item_id, weight in matrix.get(user.id, {}).items() if weight > 0}
    return {
        "user_item_matrix": {
            "users": len(matrix),
            "items": len({item_id for row in matrix.values() for item_id in row}),
            "current_user": matrix.get(user.id, {}),
        },
        "candidate_generation": {
            "count": len(ranked),
            "sources": sorted({source for item in ranked for source in item["candidate_sources"]}),
        },
        "ranking": {
            "top_k_ids": recommended_ids[:k],
            "embedding_backend": "sentence-transformers" if _sentence_model() is not None else "token-cosine-fallback",
            "cold_start": not relevant_ids and not profile_text_for_diagnostics(profile, user),
        },
        "metrics": {
            "evaluation": "observed positive interactions",
            "k": k,
            "precision_at_k": round(precision_at_k(recommended_ids, relevant_ids, k), 4),
            "recall_at_k": round(recall_at_k(recommended_ids, relevant_ids, k), 4),
            "ndcg_at_k": round(ndcg_at_k(recommended_ids, relevant_ids, k), 4),
        },
    }


def profile_text_for_diagnostics(profile, user):
    return any([
        profile.current_role, profile.degree, profile.branch, profile.target_roles, user.skills,
    ])


@router.post("/{opportunity_id}/interact")
def record_interaction(
    opportunity_id: int,
    data: InteractionIn,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if not db.get(Opportunity, opportunity_id):
        raise HTTPException(status_code=404, detail="Opportunity not found")
    db.add(Interaction(user_id=user.id, opportunity_id=opportunity_id, event_type=data.event_type))
    db.commit()
    return {"recorded": True, "event_type": data.event_type}


@router.get("/recommendation-preferences")
def get_recommendation_preferences(user=Depends(get_current_user), db: Session = Depends(get_db)):
    preference = user.recommendation_preferences
    if not preference:
        preference = RecommendationPreference(user_id=user.id)
        db.add(preference)
        db.commit()
    return {"target_companies": [item for item in (preference.target_companies or "").split(",") if item], "target_seniority": preference.target_seniority}


@router.put("/recommendation-preferences")
def update_recommendation_preferences(data: RecommendationPreferenceIn, user=Depends(get_current_user), db: Session = Depends(get_db)):
    preference = user.recommendation_preferences
    if not preference:
        preference = RecommendationPreference(user_id=user.id)
        db.add(preference)
    preference.target_companies = ",".join(item.strip() for item in data.target_companies if item.strip())
    preference.target_seniority = data.target_seniority
    db.commit()
    return {"updated": True}


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
    application = (
        db.query(Application)
        .filter(Application.user_id == user.id, Application.opportunity_id == opportunity_id)
        .first()
    )
    if not application:
        db.add(Application(user_id=user.id, opportunity_id=opportunity_id, status="saved"))
    db.add(Interaction(user_id=user.id, opportunity_id=opportunity_id, event_type="save"))
    db.commit()

    return {"saved": True}
