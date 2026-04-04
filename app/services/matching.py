import json

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Goal, Profile
from app.services.groq_client import chat_json


def prefilter_profiles(goal: Goal, db: Session) -> list[tuple[Profile, float]]:
    """Score all profiles by keyword/tag overlap with the goal. Return top N."""
    target_roles = [r.lower() for r in goal.get_target_roles()]
    target_companies = [c.lower() for c in goal.get_target_companies()]
    goal_text = f"{goal.description} {goal.user_background} {goal.goal_type}".lower()
    goal_words = set(goal_text.split())

    profiles = db.query(Profile).all()
    scored = []

    for p in profiles:
        score = 0.0
        role_lower = p.role.lower()
        company_lower = p.company.lower()
        skills = [s.lower() for s in p.get_skills()]
        tags = [t.lower() for t in p.get_career_tags()]

        # Role match
        for tr in target_roles:
            if tr in role_lower:
                score += 3.0
            elif any(word in role_lower for word in tr.split()):
                score += 1.5

        # Company match
        for tc in target_companies:
            if tc in company_lower:
                score += 3.0

        # Skill overlap with goal text
        for skill in skills:
            if skill in goal_text:
                score += 1.0

        # Tag overlap with goal words
        for tag in tags:
            if tag in goal_words:
                score += 0.5

        # Seniority bonus based on goal type
        if goal.goal_type in ("mentorship", "informational"):
            if p.seniority in ("senior", "exec"):
                score += 1.0
        elif goal.goal_type == "investor":
            if any(t in tags for t in ["investor", "venture-capital"]):
                score += 3.0
        elif goal.goal_type == "cofounder":
            if any(t in tags for t in ["startup", "entrepreneur", "founder"]):
                score += 2.0

        if score > 0:
            scored.append((p, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:settings.MAX_PROFILES_PER_RANK]


def ai_rank_profiles(goal: Goal, prefiltered: list[tuple[Profile, float]]) -> list[dict]:
    """Use Groq to rank and score prefiltered profiles. Returns list of {profile_id, score, reason}."""
    if not prefiltered:
        return []

    profiles_summary = []
    for p, pre_score in prefiltered:
        profiles_summary.append({
            "id": p.id,
            "name": p.name,
            "role": p.role,
            "company": p.company,
            "seniority": p.seniority,
            "skills": p.get_skills(),
            "location": p.location,
        })

    system_prompt = """You are a networking match scorer. Given a user's career goal and a list of professionals,
rank them by how valuable a connection would be. Consider role relevance, company fit, seniority level,
and skill overlap. Return a JSON object with a "rankings" array, each item having:
- "id": the profile id
- "score": 0-100 match score
- "reason": one sentence explaining why this person is a good match

Return the top 20 best matches, sorted by score descending."""

    user_prompt = f"""Goal: {goal.goal_type}
Description: {goal.description}
Background: {goal.user_background}
Target roles: {json.dumps(goal.get_target_roles())}
Target companies: {json.dumps(goal.get_target_companies())}

Candidates:
{json.dumps(profiles_summary, indent=1)}"""

    result = chat_json(system_prompt, user_prompt)
    return result.get("rankings", [])


def get_ranked_contacts(goal: Goal, db: Session) -> list[dict]:
    """Full pipeline: prefilter → AI rank → return enriched results."""
    prefiltered = prefilter_profiles(goal, db)

    if not prefiltered:
        return []

    try:
        rankings = ai_rank_profiles(goal, prefiltered)
    except Exception:
        # Fallback to prefilter scores if Groq fails
        rankings = [
            {"id": p.id, "score": round(pre_score * 10, 1), "reason": "Matched by role, skills, and experience"}
            for p, pre_score in prefiltered[:20]
        ]

    # Enrich with full profile data
    profile_map = {p.id: p for p, _ in prefiltered}
    results = []
    for r in rankings:
        profile = profile_map.get(r["id"])
        if profile:
            results.append({
                "profile": profile,
                "score": r["score"],
                "reason": r["reason"],
            })

    return results
