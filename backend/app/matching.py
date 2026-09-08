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

INTERACTION_WEIGHTS = {
    "impression": 0.1,
    "view": 1.0,
    "save": 3.0,
    "apply": 4.0,
    "dismiss": -2.0,
}


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


def interaction_weight(event_type):
    return INTERACTION_WEIGHTS.get((event_type or "").lower(), 0.0)


def build_interaction_matrix(interactions):
    """Return a sparse user -> item -> weighted interaction matrix."""
    matrix = {}
    for interaction in interactions:
        user_matrix = matrix.setdefault(interaction.user_id, {})
        item_id = interaction.opportunity_id
        user_matrix[item_id] = user_matrix.get(item_id, 0.0) + interaction_weight(interaction.event_type)
    return matrix


def _profile_signal(profile, user):
    return any([
        profile.current_role, profile.degree, profile.branch, profile.target_roles, user.skills,
    ])


def _item_similarity(left, right):
    return _token_similarity(opportunity_text(left), opportunity_text(right))


def learned_preference_score(op, positive_items):
    if not positive_items:
        return 0.0
    score = 0.0
    for item in positive_items:
        if normalize_text(item.organization) == normalize_text(op.organization):
            score = max(score, 1.0)
        elif normalize_text(item.opportunity_type) == normalize_text(op.opportunity_type):
            score = max(score, 0.6)
        elif normalize_text(item.role) == normalize_text(op.role):
            score = max(score, 0.4)
    return score


def seniority_compatibility(op, profile, preference=None):
    experience = profile.years_experience or 0
    target = getattr(preference, "target_seniority", "auto") if preference else "auto"
    if target == "auto":
        target = "intern" if experience == 0 else "junior" if experience <= 2 else "mid" if experience <= 5 else "senior"
    ranges = {"intern": (0, 1), "junior": (0, 3), "mid": (2, 6), "senior": (5, 20), "lead": (8, 30)}
    minimum, maximum = ranges.get(target, (0, 30))
    opportunity_min = op.experience_min or 0
    opportunity_max = op.experience_max or max(opportunity_min, 30)
    return 1.0 if opportunity_max >= minimum and opportunity_min <= maximum else 0.0


def candidate_generation(profile, user, opportunities, interactions, preference=None, limit=100):
    """Generate candidates from content, history similarity, and global popularity."""
    matrix = build_interaction_matrix(interactions)
    user_history = matrix.get(user.id, {})
    positive_history = {item_id: weight for item_id, weight in user_history.items() if weight > 0}
    opportunities_by_id = {op.id: op for op in opportunities}
    positive_items = [opportunities_by_id[item_id] for item_id, weight in positive_history.items() if item_id in opportunities_by_id and weight > 0]
    popularity = {}
    for user_items in matrix.values():
        for item_id, weight in user_items.items():
            popularity[item_id] = popularity.get(item_id, 0.0) + max(0.0, weight)
    max_popularity = max(popularity.values(), default=1.0)
    cold_start = not positive_history and not _profile_signal(profile, user)

    candidates = []
    for op in opportunities:
        content_score = semantic_similarity(profile, user, op) if _profile_signal(profile, user) else 0.0
        history_score = 0.0
        for item_id, weight in positive_history.items():
            history_item = opportunities_by_id.get(item_id)
            if history_item and item_id != op.id:
                history_score = max(history_score, min(1.0, weight / 4.0) * _item_similarity(op, history_item))
        popularity_score = popularity.get(op.id, 0.0) / max_popularity
        learned_score = learned_preference_score(op, positive_items)
        target_companies = csv_values(preference.target_companies) if preference else set()
        company_score = 1.0 if target_companies and normalize_text(op.organization) in target_companies else 0.0
        seniority_score = seniority_compatibility(op, profile, preference)
        sources = []
        if content_score > 0:
            sources.append("content")
        if history_score > 0:
            sources.append("interaction")
        if popularity_score > 0:
            sources.append("popular")
        if cold_start:
            sources = ["cold_start"]
        candidate_score = max(content_score, history_score, popularity_score * 0.5)
        candidate_score = max(candidate_score, learned_score * 0.7, company_score * 0.9)
        candidates.append({
            "opportunity": op,
            "content_score": content_score,
            "interaction_score": history_score,
            "popularity_score": popularity_score,
            "learned_preference_score": learned_score,
            "target_company_score": company_score,
            "seniority_score": seniority_score,
            "candidate_sources": sources,
            "candidate_score": candidate_score,
        })

    candidates.sort(key=lambda item: (-item["candidate_score"], item["opportunity"].id))
    return candidates[:limit]


def rank_candidates(candidates, score_function):
    """Combine business/profile score with retrieval features into a 0-100 rank."""
    ranked = []
    for candidate in candidates:
        base_score, reasons, semantic_score = score_function(candidate["opportunity"])
        rank_score = (
            0.40 * (base_score / 100)
            + 0.20 * candidate["content_score"]
            + 0.15 * candidate["interaction_score"]
            + 0.05 * candidate["popularity_score"]
            + 0.10 * candidate.get("learned_preference_score", 0)
            + 0.05 * candidate.get("target_company_score", 0)
            + 0.05 * candidate.get("seniority_score", 0)
        )
        candidate = {**candidate, "base_score": base_score, "rank_score": round(rank_score * 100),
                     "reasons": reasons, "semantic_score": semantic_score}
        ranked.append(candidate)
    ranked.sort(key=lambda item: (-item["rank_score"], item["opportunity"].id))
    return ranked


def precision_at_k(recommended_ids, relevant_ids, k):
    if k <= 0:
        return 0.0
    recommended = recommended_ids[:k]
    return sum(item_id in relevant_ids for item_id in recommended) / k


def recall_at_k(recommended_ids, relevant_ids, k):
    if not relevant_ids:
        return 0.0
    return sum(item_id in relevant_ids for item_id in recommended_ids[:k]) / len(relevant_ids)


def ndcg_at_k(recommended_ids, relevant_ids, k):
    recommended = recommended_ids[:k]
    dcg = sum(1 / math.log2(position + 2) for position, item_id in enumerate(recommended) if item_id in relevant_ids)
    ideal_hits = min(len(relevant_ids), k)
    ideal_dcg = sum(1 / math.log2(position + 2) for position in range(ideal_hits))
    return dcg / ideal_dcg if ideal_dcg else 0.0
