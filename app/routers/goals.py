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
