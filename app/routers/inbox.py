from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Goal, Message, Reply
from app.services.inbox import suggest_follow_up
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
    reply = db.query(Reply).filter(Reply.id == reply_id).first()
    if reply and reply.follow_up_status == "pending":
        reply.follow_up_status = "sent"
        db.commit()
        db.refresh(reply)
    return templates.TemplateResponse(request, "partials/reply_card.html", {"reply": reply})


@router.post("/replies/{reply_id}/skip-followup")
async def skip_follow_up(request: Request, reply_id: int, db: Session = Depends(get_db)):
    reply = db.query(Reply).filter(Reply.id == reply_id).first()
    if reply and reply.follow_up_status == "pending":
        reply.follow_up_status = "skipped"
        db.commit()
        db.refresh(reply)
    return templates.TemplateResponse(request, "partials/reply_card.html", {"reply": reply})


@router.get("/replies/{reply_id}/edit-followup")
async def edit_followup_form(request: Request, reply_id: int, db: Session = Depends(get_db)):
    reply = db.query(Reply).filter(Reply.id == reply_id).first()
    html = f"""
    <form hx-patch="/api/replies/{reply.id}/followup" hx-target="#reply-{reply.id}" hx-swap="outerHTML">
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
    return templates.TemplateResponse(request, "partials/reply_card.html", {"reply": reply})
