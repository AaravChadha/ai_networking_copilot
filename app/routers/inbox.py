from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Goal, Message, Reply
from app.services.inbox import continue_conversation
from app.templating import templates

router = APIRouter(prefix="/api", tags=["inbox"])


@router.get("/goals/{goal_id}/inbox")
async def get_inbox(request: Request, goal_id: int, db: Session = Depends(get_db)):
    """Get all replies for a goal's sent messages."""
    replies = (
        db.query(Reply)
        .join(Message, Reply.message_id == Message.id)
        .filter(Message.goal_id == goal_id)
        .all()
    )
    return replies


@router.post("/replies/{reply_id}/follow-up")
async def send_follow_up(request: Request, reply_id: int, db: Session = Depends(get_db)):
    """Send a follow-up and continue the conversation."""
    reply = db.query(Reply).filter(Reply.id == reply_id).first()
    if not reply or reply.follow_up_status != "pending":
        return templates.TemplateResponse(request, "partials/thread_card.html", {
            "thread": _get_thread(reply.message_id, db),
        })

    # Use the follow-up suggestion as the body (may have been edited)
    follow_up_body = reply.follow_up_suggestion

    # Continue the conversation — saves outbound, generates new inbound reply
    continue_conversation(reply.id, follow_up_body, db)

    thread = _get_thread(reply.message_id, db)
    return templates.TemplateResponse(request, "partials/thread_card.html", {"thread": thread})


@router.post("/replies/{reply_id}/skip-followup")
async def skip_follow_up(request: Request, reply_id: int, db: Session = Depends(get_db)):
    reply = db.query(Reply).filter(Reply.id == reply_id).first()
    if reply and reply.follow_up_status == "pending":
        reply.follow_up_status = "skipped"
        db.commit()
        db.refresh(reply)
    thread = _get_thread(reply.message_id, db)
    return templates.TemplateResponse(request, "partials/thread_card.html", {"thread": thread})


@router.get("/replies/{reply_id}/edit-followup")
async def edit_followup_form(request: Request, reply_id: int, db: Session = Depends(get_db)):
    reply = db.query(Reply).filter(Reply.id == reply_id).first()
    html = f"""
    <form hx-patch="/api/replies/{reply.id}/followup" hx-target="#thread-{reply.message_id}" hx-swap="outerHTML">
        <textarea name="follow_up_suggestion" rows="4">{reply.follow_up_suggestion}</textarea>
        <div style="display: flex; gap: 0.5rem; margin-top: 0.5rem;">
            <button type="submit">Save</button>
            <button type="button" class="outline secondary"
                hx-get="/api/replies/{reply.id}/cancel-edit-followup"
                hx-target="#followup-body-{reply.id}" hx-swap="innerHTML">Cancel</button>
        </div>
    </form>
    """
    return HTMLResponse(html)


@router.get("/replies/{reply_id}/cancel-edit-followup")
async def cancel_edit_followup(request: Request, reply_id: int, db: Session = Depends(get_db)):
    reply = db.query(Reply).filter(Reply.id == reply_id).first()
    html = f'<p style="white-space: pre-wrap; font-size: 0.9rem; opacity: 0.85;">{reply.follow_up_suggestion}</p>'
    return HTMLResponse(html)


@router.patch("/replies/{reply_id}/followup")
async def update_followup(request: Request, reply_id: int, db: Session = Depends(get_db)):
    reply = db.query(Reply).filter(Reply.id == reply_id).first()
    form = await request.form()
    if "follow_up_suggestion" in form:
        reply.follow_up_suggestion = form["follow_up_suggestion"]
    db.commit()
    db.refresh(reply)
    thread = _get_thread(reply.message_id, db)
    return templates.TemplateResponse(request, "partials/thread_card.html", {"thread": thread})


def _get_thread(message_id: int, db: Session) -> dict:
    """Build a thread dict for template rendering."""
    message = db.query(Message).filter(Message.id == message_id).first()
    replies = (
        db.query(Reply)
        .filter(Reply.message_id == message_id)
        .order_by(Reply.round_number)
        .all()
    )
    # Latest inbound reply determines the thread sentiment
    inbound = [r for r in replies if r.direction == "inbound"]
    latest_inbound = inbound[-1] if inbound else None
    return {
        "message": message,
        "replies": replies,
        "latest_inbound": latest_inbound,
        "sentiment": latest_inbound.sentiment if latest_inbound else "neutral",
        "is_concluded": latest_inbound.is_conclusion if latest_inbound else False,
    }
