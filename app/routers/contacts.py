from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Goal
from app.services.matching import get_ranked_contacts

router = APIRouter(prefix="/api/goals", tags=["contacts"])


@router.get("/{goal_id}/matches")
async def get_matches(goal_id: int, db: Session = Depends(get_db)):
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        return {"error": "Goal not found"}

    contacts = get_ranked_contacts(goal, db)
    return [
        {
            "profile_id": c["profile"].id,
            "name": c["profile"].name,
            "role": c["profile"].role,
            "company": c["profile"].company,
            "score": c["score"],
            "reason": c["reason"],
        }
        for c in contacts
    ]
