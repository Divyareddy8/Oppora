import math
import re
from collections import Counter
from functools import lru_cache


KNOWN_COMPANY_TIERS = {
    "google": "S",
    "microsoft": "S",
    "amazon": "S",
    "meta": "S",
    "apple": "S",
    "iit": "S",
    "iisc": "S",
    "isro": "S",
    "drdo": "S",
    "adobe": "A",
    "ibm": "A",
    "intel": "A",
    "oracle": "A",
}

TOKEN_RE = re.compile(r"[a-z0-9+#.]+", re.IGNORECASE)


def normalize_text(value):
    return " ".join(TOKEN_RE.findall((value or "").lower()))


def csv_values(value):
    return {normalize_text(item) for item in (value or "").split(",") if normalize_text(item)}


def opportunity_fingerprint(op):
    """Create a stable identity for duplicate listings from different sources."""
    title = normalize_text(op.title)
    organization = normalize_text(op.organization)
    role = normalize_text(op.role)
    location = normalize_text(op.location)
    return (organization, title, role, location)


def inferred_company_tier(op):
    current = (op.company_tier or "").strip()
    if current and current.lower() != "unrated":
        return current

    organization = normalize_text(op.organization)
    for name, tier in KNOWN_COMPANY_TIERS.items():
        if name in organization:
            return tier
    return "Unrated"


def profile_text(profile, user):
    return " ".join(
        value
        for value in [
            profile.current_role,
            profile.degree,
            profile.branch,
            profile.target_roles,
            profile.preferred_types,
            " ".join(skill.name for skill in user.skills),
        ]
        if value
    )


def opportunity_text(op):
    return " ".join(
        value
        for value in [
            op.title,
            op.organization,
            op.opportunity_type,
            op.role,
            op.description,
            op.location,
            " ".join(skill.name for skill in op.skills),
        ]
        if value
    )


@lru_cache(maxsize=1)
def _sentence_model():
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        return None
    try:
        return SentenceTransformer("all-MiniLM-L6-v2")
    except Exception:
        return None


def _token_similarity(left, right):
    left_counts = Counter(TOKEN_RE.findall(normalize_text(left)))
    right_counts = Counter(TOKEN_RE.findall(normalize_text(right)))
    if not left_counts or not right_counts:
        return 0.0

    shared = set(left_counts) & set(right_counts)
    numerator = sum(left_counts[token] * right_counts[token] for token in shared)
    denominator = math.sqrt(sum(value * value for value in left_counts.values())) * math.sqrt(
        sum(value * value for value in right_counts.values())
    )
    return numerator / denominator if denominator else 0.0


def semantic_similarity(profile, user, op):
    profile_content = profile_text(profile, user)
    opportunity_content = opportunity_text(op)
    model = _sentence_model()
    if model is not None:
        try:
            vectors = model.encode([profile_content, opportunity_content], normalize_embeddings=True)
            return max(0.0, min(1.0, float(vectors[0] @ vectors[1])))
        except Exception:
            pass
    return _token_similarity(profile_content, opportunity_content)


def matching_skills(user, op):
    user_skills = {normalize_text(skill.name): skill.name for skill in user.skills}
    return sorted(
        {user_skills[normalize_text(skill.name)] for skill in op.skills if normalize_text(skill.name) in user_skills},
        key=str.lower,
    )
