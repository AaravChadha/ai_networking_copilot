import json

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.templating import templates
from app.models import Goal, SendConfig
from app.services.matching import get_ranked_contacts

router = APIRouter()


@router.get("/")
async def dashboard(request: Request, db: Session = Depends(get_db)):
    goals = db.query(Goal).order_by(Goal.created_at.desc()).all()
    return templates.TemplateResponse(request, "dashboard.html", {
        "goals": goals,
    })


@router.get("/goals/new")
async def goal_setup(request: Request):
    return templates.TemplateResponse(request, "goal_setup.html", {})


@router.post("/goals/new")
async def create_goal_form(
    request: Request,
    goal_type: str = Form(...),
    description: str = Form(...),
    user_background: str = Form(""),
    target_roles: str = Form(""),
    target_companies: str = Form(""),
    db: Session = Depends(get_db),
):
    roles = [r.strip() for r in target_roles.split(",") if r.strip()]
    companies = [c.strip() for c in target_companies.split(",") if c.strip()]

    goal = Goal(
        goal_type=goal_type,
        description=description,
        user_background=user_background,
        target_roles=json.dumps(roles),
        target_companies=json.dumps(companies),
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)

    db.add(SendConfig(goal_id=goal.id))
    db.commit()

    return RedirectResponse(url=f"/goals/{goal.id}/contacts", status_code=303)


@router.get("/goals/{goal_id}/contacts")
async def contacts_page(request: Request, goal_id: int, db: Session = Depends(get_db)):
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    contacts = get_ranked_contacts(goal, db)
    return templates.TemplateResponse(request, "contacts.html", {
        "goal": goal,
        "contacts": contacts,
    })


@router.post("/goals/{goal_id}/templates")
async def templates_page_post(
    request: Request,
    goal_id: int,
    profile_ids: list[int] = Form([]),
    db: Session = Depends(get_db),
):
    # Store selected profile IDs in session via query params for now
    ids = ",".join(str(i) for i in profile_ids)
    return RedirectResponse(url=f"/goals/{goal_id}/templates?profiles={ids}", status_code=303)


@router.get("/goals/{goal_id}/templates")
async def templates_page_get(request: Request, goal_id: int, profiles: str = "", db: Session = Depends(get_db)):
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    profile_ids = [int(x) for x in profiles.split(",") if x.strip()]
    return templates.TemplateResponse(request, "template_editor.html", {
        "goal": goal,
        "profile_ids": profile_ids,
    })
