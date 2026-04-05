import json

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.templating import templates
from app.models import Goal, Message, OutreachTemplate, Reply, SendConfig
from app.services.matching import get_ranked_contacts
from app.services.outreach import batch_generate
from app.services.templates import get_templates

router = APIRouter()


@router.get("/")
async def dashboard(request: Request, db: Session = Depends(get_db)):
    goals = db.query(Goal).order_by(Goal.created_at.desc()).all()

    # Aggregate stats across all campaigns
    all_messages = db.query(Message).all()
    total_sent = sum(1 for m in all_messages if m.status in ("sent", "replied"))
    msg_ids = [m.id for m in all_messages]
    all_inbound = (
        db.query(Reply)
        .filter(Reply.message_id.in_(msg_ids), Reply.direction == "inbound")
        .all()
    ) if msg_ids else []
    total_replies = len({r.message_id for r in all_inbound})
    total_reply_rate = round(total_replies / total_sent * 100, 1) if total_sent > 0 else 0
    total_pending = sum(1 for r in all_inbound if r.follow_up_status == "pending")

    # Per-goal stats
    goal_stats = {}
    for goal in goals:
        msgs = [m for m in all_messages if m.goal_id == goal.id]
        sent = sum(1 for m in msgs if m.status in ("sent", "replied"))
        g_ids = [m.id for m in msgs]
        inbound = [r for r in all_inbound if r.message_id in set(g_ids)]
        replies = len({r.message_id for r in inbound})
        pending = sum(1 for m in msgs if m.status in ("draft", "approved"))
        sent_only = sum(1 for m in msgs if m.status == "sent")
        replied = sum(1 for m in msgs if m.status == "replied")
        goal_stats[goal.id] = {
            "total": len(msgs),
            "pending": pending,
            "sent": sent,
            "sent_only": sent_only,
            "replied": replied,
            "replies": replies,
            "reply_rate": round(replies / sent * 100, 1) if sent > 0 else 0,
            "positive": sum(1 for r in inbound if r.sentiment == "positive"),
            "neutral": sum(1 for r in inbound if r.sentiment == "neutral"),
            "negative": sum(1 for r in inbound if r.sentiment == "negative"),
        }

    return templates.TemplateResponse(request, "dashboard.html", {
        "goals": goals,
        "total_sent": total_sent,
        "total_replies": total_replies,
        "total_reply_rate": total_reply_rate,
        "total_pending": total_pending,
        "goal_stats": goal_stats,
        "active_page": "dashboard",
    })


@router.get("/goals/new")
async def goal_setup(request: Request):
    return templates.TemplateResponse(request, "goal_setup.html", {"active_page": "goals"})


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
    # Profile IDs that already have messages for this goal
    existing_ids = {
        m.profile_id
        for m in db.query(Message).filter(Message.goal_id == goal_id).all()
    }
    return templates.TemplateResponse(request, "contacts.html", {
        "goal": goal,
        "contacts": contacts,
        "existing_profile_ids": existing_ids,
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
    outreach_templates = get_templates(db, goal_id)
    # Find the last used template for this campaign
    last_msg = (
        db.query(Message)
        .filter(Message.goal_id == goal_id, Message.template_id.isnot(None))
        .order_by(Message.created_at.desc())
        .first()
    )
    last_template_id = last_msg.template_id if last_msg else None
    return templates.TemplateResponse(request, "template_editor.html", {
        "goal": goal,
        "profile_ids": profile_ids,
        "outreach_templates": outreach_templates,
        "last_template_id": last_template_id,
    })


@router.post("/goals/{goal_id}/generate")
async def generate_messages(
    request: Request,
    goal_id: int,
    template_id: int = Form(...),
    tone: str = Form("professional"),
    profile_ids: list[int] = Form([]),
    intro_override: str = Form(""),
    context_override: str = Form(""),
    ask_override: str = Form(""),
    closing_override: str = Form(""),
    db: Session = Depends(get_db),
):
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    template = db.query(OutreachTemplate).filter(OutreachTemplate.id == template_id).first()

    batch_generate(
        goal, profile_ids, template, tone,
        intro_override, context_override, ask_override, closing_override, db,
    )

    return RedirectResponse(url=f"/goals/{goal_id}/outreach", status_code=303)


@router.get("/goals/{goal_id}/outreach")
async def outreach_page(request: Request, goal_id: int, db: Session = Depends(get_db)):
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    messages = db.query(Message).filter(Message.goal_id == goal_id).all()
    return templates.TemplateResponse(request, "outreach.html", {
        "goal": goal,
        "messages": messages,
    })


@router.get("/inbox")
async def inbox_all(request: Request, db: Session = Depends(get_db)):
    threads = _build_threads(db)
    return templates.TemplateResponse(request, "inbox.html", {
        "goal": None,
        "threads": threads,
        "active_page": "inbox",
    })


@router.get("/goals/{goal_id}/inbox")
async def inbox_page(request: Request, goal_id: int, db: Session = Depends(get_db)):
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    threads = _build_threads(db, goal_id)
    return templates.TemplateResponse(request, "inbox.html", {
        "goal": goal,
        "threads": threads,
        "active_page": "inbox",
    })


@router.get("/goals/{goal_id}/inbox/{message_id}")
async def chat_page(request: Request, goal_id: int, message_id: int, db: Session = Depends(get_db)):
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    threads = _build_threads(db, goal_id)
    # Find the active thread
    active_thread = next((t for t in threads if t["message"].id == message_id), None)
    return templates.TemplateResponse(request, "chat.html", {
        "goal": goal,
        "threads": threads,
        "active_thread": active_thread,
        "active_message_id": message_id,
    })


def _build_threads(db: Session, goal_id: int = None) -> list[dict]:
    """Group replies into conversation threads by message."""
    query = db.query(Reply).join(Message, Reply.message_id == Message.id)
    if goal_id:
        query = query.filter(Message.goal_id == goal_id)
    all_replies = query.order_by(Reply.round_number).all()

    # Group by message_id
    threads_map = {}
    for reply in all_replies:
        if reply.message_id not in threads_map:
            threads_map[reply.message_id] = []
        threads_map[reply.message_id].append(reply)

    threads = []
    for message_id, replies in threads_map.items():
        message = db.query(Message).filter(Message.id == message_id).first()
        inbound = [r for r in replies if r.direction == "inbound"]
        latest_inbound = inbound[-1] if inbound else None
        # Last message in the thread (inbound or outbound)
        last_reply = replies[-1] if replies else None
        last_preview = (last_reply.body[:80] + "...") if last_reply and len(last_reply.body) > 80 else (last_reply.body if last_reply else "")
        threads.append({
            "message": message,
            "replies": replies,
            "latest_inbound": latest_inbound,
            "sentiment": latest_inbound.sentiment if latest_inbound else "neutral",
            "is_concluded": latest_inbound.is_conclusion if latest_inbound else False,
            "reply_count": len(replies),
            "last_preview": last_preview,
        })

    return threads
