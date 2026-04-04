from datetime import datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Goal, Message
from app.services.inbox import generate_replies_for_sent
from app.templating import templates

router = APIRouter(prefix="/api", tags=["messages"])


@router.post("/messages/{message_id}/approve")
async def approve_message(request: Request, message_id: int, db: Session = Depends(get_db)):
    msg = db.query(Message).filter(Message.id == message_id).first()
    if msg and msg.status == "draft":
        msg.status = "approved"
        db.commit()
        db.refresh(msg)
    return templates.TemplateResponse(request, "partials/message_card.html", {"msg": msg})


@router.post("/messages/{message_id}/send")
async def send_message(request: Request, message_id: int, db: Session = Depends(get_db)):
    msg = db.query(Message).filter(Message.id == message_id).first()
    if msg and msg.status == "approved":
        msg.status = "sent"
        msg.sent_at = datetime.utcnow()
        db.commit()
        db.refresh(msg)
        # Generate synthetic reply for demo
        generate_replies_for_sent([msg], db)
        db.refresh(msg)
    return templates.TemplateResponse(request, "partials/message_card.html", {"msg": msg})


@router.get("/messages/{message_id}/edit")
async def edit_message_form(request: Request, message_id: int, db: Session = Depends(get_db)):
    msg = db.query(Message).filter(Message.id == message_id).first()
    html = f"""
    <form hx-patch="/api/messages/{msg.id}" hx-target="#message-{msg.id}" hx-swap="outerHTML">
        <input type="text" name="subject" value="{msg.subject}" style="margin-bottom: 0.5rem;">
        <textarea name="body" rows="8">{msg.body}</textarea>
        <div style="display: flex; gap: 0.5rem; margin-top: 0.5rem;">
            <button type="submit">Save</button>
            <button type="button" class="outline secondary" hx-get="/api/messages/{msg.id}/cancel-edit" hx-target="#body-display-{msg.id}" hx-swap="innerHTML">Cancel</button>
        </div>
    </form>
    """
    return HTMLResponse(html)


@router.get("/messages/{message_id}/cancel-edit")
async def cancel_edit(request: Request, message_id: int, db: Session = Depends(get_db)):
    msg = db.query(Message).filter(Message.id == message_id).first()
    html = f'<p style="white-space: pre-wrap;">{msg.body}</p>'
    return HTMLResponse(html)


@router.patch("/messages/{message_id}")
async def update_message(request: Request, message_id: int, db: Session = Depends(get_db)):
    msg = db.query(Message).filter(Message.id == message_id).first()
    form = await request.form()
    if "subject" in form:
        msg.subject = form["subject"]
    if "body" in form:
        msg.body = form["body"]
    db.commit()
    db.refresh(msg)
    return templates.TemplateResponse(request, "partials/message_card.html", {"msg": msg})


@router.post("/goals/{goal_id}/approve-all")
async def approve_all(request: Request, goal_id: int, db: Session = Depends(get_db)):
    db.query(Message).filter(
        Message.goal_id == goal_id, Message.status == "draft"
    ).update({"status": "approved"})
    db.commit()
    messages = db.query(Message).filter(Message.goal_id == goal_id).all()
    return templates.TemplateResponse(request, "partials/message_list.html", {"messages": messages})


@router.post("/goals/{goal_id}/send-batch")
async def send_batch(request: Request, goal_id: int, db: Session = Depends(get_db)):
    db.query(Message).filter(
        Message.goal_id == goal_id, Message.status == "approved"
    ).update({"status": "sent", "sent_at": datetime.utcnow()})
    db.commit()
    messages = db.query(Message).filter(Message.goal_id == goal_id).all()
    # Generate synthetic replies for demo
    sent_messages = [m for m in messages if m.status == "sent"]
    generate_replies_for_sent(sent_messages, db)
    # Refresh to pick up status changes
    messages = db.query(Message).filter(Message.goal_id == goal_id).all()
    return templates.TemplateResponse(request, "partials/message_list.html", {"messages": messages})
