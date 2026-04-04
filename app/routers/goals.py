import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from fastapi.responses import HTMLResponse

from app.models import CachedRanking, Goal, Message, Reply, SendConfig
from app.schemas import GoalCreate, GoalResponse

router = APIRouter(prefix="/api/goals", tags=["goals"])


@router.post("/", response_model=GoalResponse)
async def create_goal(goal: GoalCreate, db: Session = Depends(get_db)):
    db_goal = Goal(
        goal_type=goal.goal_type,
        description=goal.description,
        user_background=goal.user_background,
        target_roles=json.dumps(goal.target_roles),
        target_companies=json.dumps(goal.target_companies),
    )
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)

    # Create default send config
    db.add(SendConfig(goal_id=db_goal.id))
    db.commit()

    return _goal_to_response(db_goal)


@router.get("/", response_model=list[GoalResponse])
async def list_goals(db: Session = Depends(get_db)):
    goals = db.query(Goal).order_by(Goal.created_at.desc()).all()
    return [_goal_to_response(g) for g in goals]


@router.get("/{goal_id}", response_model=GoalResponse)
async def get_goal(goal_id: int, db: Session = Depends(get_db)):
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    return _goal_to_response(goal)


@router.get("/{goal_id}/stats")
async def get_goal_stats(goal_id: int, db: Session = Depends(get_db)):
    """Get campaign stats: messages sent, reply rate, sentiment breakdown, pending follow-ups."""
    messages = db.query(Message).filter(Message.goal_id == goal_id).all()
    total = len(messages)
    sent = sum(1 for m in messages if m.status in ("sent", "replied"))
    drafts = sum(1 for m in messages if m.status == "draft")
    approved = sum(1 for m in messages if m.status == "approved")

    # Get all inbound replies for this goal
    msg_ids = [m.id for m in messages]
    replies = (
        db.query(Reply)
        .filter(Reply.message_id.in_(msg_ids), Reply.direction == "inbound")
        .all()
    ) if msg_ids else []

    replied_message_ids = {r.message_id for r in replies}
    reply_rate = (len(replied_message_ids) / sent * 100) if sent > 0 else 0

    positive = sum(1 for r in replies if r.sentiment == "positive")
    neutral = sum(1 for r in replies if r.sentiment == "neutral")
    negative = sum(1 for r in replies if r.sentiment == "negative")
    pending_followups = sum(1 for r in replies if r.follow_up_status == "pending")

    return {
        "total_messages": total,
        "drafts": drafts,
        "approved": approved,
        "sent": sent,
        "replies": len(replied_message_ids),
        "reply_rate": round(reply_rate, 1),
        "positive": positive,
        "neutral": neutral,
        "negative": negative,
        "pending_followups": pending_followups,
    }


@router.delete("/{goal_id}")
async def delete_goal(goal_id: int, db: Session = Depends(get_db)):
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        return HTMLResponse("")

    # Delete related data
    db.query(CachedRanking).filter(CachedRanking.goal_id == goal_id).delete()
    for msg in db.query(Message).filter(Message.goal_id == goal_id).all():
        db.query(Reply).filter(Reply.message_id == msg.id).delete()
    db.query(Message).filter(Message.goal_id == goal_id).delete()
    db.query(SendConfig).filter(SendConfig.goal_id == goal_id).delete()
    db.delete(goal)
    db.commit()

    return HTMLResponse("")


def _goal_to_response(goal: Goal) -> GoalResponse:
    return GoalResponse(
        id=goal.id,
        goal_type=goal.goal_type,
        description=goal.description,
        user_background=goal.user_background,
        target_roles=json.loads(goal.target_roles),
        target_companies=json.loads(goal.target_companies),
        status=goal.status,
        created_at=goal.created_at,
    )
