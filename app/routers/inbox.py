from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from datetime import datetime

from app.database import get_db
from app.models import Goal, Message, Profile, Reply
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


@router.get("/replies/{reply_id}/compose")
async def compose_follow_up(request: Request, reply_id: int, db: Session = Depends(get_db)):
    """Show editable textarea pre-filled with the AI suggestion, with confirm/cancel."""
    reply = db.query(Reply).filter(Reply.id == reply_id).first()
    html = f"""
    <form hx-post="/api/replies/{reply.id}/follow-up" hx-target="#thread-{reply.message_id}" hx-swap="outerHTML">
        <textarea name="body" rows="4" style="margin-bottom: 0.5rem;">{reply.follow_up_suggestion}</textarea>
        <div style="display: flex; gap: 0.5rem;">
            <button type="submit">Confirm Send</button>
            <button type="button" class="outline secondary"
                hx-get="/api/replies/{reply.id}/cancel-compose"
                hx-target="closest div"
                hx-swap="outerHTML">Cancel</button>
        </div>
    </form>
    """
    return HTMLResponse(html)


@router.get("/replies/{reply_id}/cancel-compose")
async def cancel_compose(request: Request, reply_id: int, db: Session = Depends(get_db)):
    """Restore the original Send Response / Skip buttons."""
    reply = db.query(Reply).filter(Reply.id == reply_id).first()
    html = f"""
    <div id="followup-actions-{reply.id}">
        <footer style="display: flex; gap: 0.5rem; margin-top: 0.5rem;">
            <button class="outline"
                hx-get="/api/replies/{reply.id}/compose"
                hx-target="#followup-actions-{reply.id}"
                hx-swap="innerHTML">
                Send Response
            </button>
            <button class="outline secondary"
                hx-post="/api/replies/{reply.id}/skip-followup"
                hx-target="#thread-{reply.message_id}"
                hx-swap="outerHTML">
                Skip
            </button>
        </footer>
    </div>
    """
    return HTMLResponse(html)


@router.post("/replies/{reply_id}/follow-up")
async def send_follow_up(request: Request, reply_id: int, db: Session = Depends(get_db)):
    """Send a follow-up and continue the conversation."""
    reply = db.query(Reply).filter(Reply.id == reply_id).first()
    if not reply or reply.follow_up_status != "pending":
        form = await request.form()
        redirect_url = form.get("redirect")
        if redirect_url:
            return RedirectResponse(url=redirect_url, status_code=303)
        return templates.TemplateResponse(request, "partials/thread_card.html", {
            "thread": _get_thread(reply.message_id, db),
        })

    # Use the edited body from the compose form, or fall back to suggestion
    form = await request.form()
    follow_up_body = form.get("body", reply.follow_up_suggestion)

    # Continue the conversation — saves outbound, generates new inbound reply
    continue_conversation(reply.id, follow_up_body, db)

    # If called from chat page, redirect back
    redirect_url = form.get("redirect")
    if redirect_url:
        return RedirectResponse(url=redirect_url, status_code=303)

    thread = _get_thread(reply.message_id, db)
    return templates.TemplateResponse(request, "partials/thread_card.html", {"thread": thread})


@router.post("/replies/{reply_id}/skip-followup")
async def skip_follow_up(request: Request, reply_id: int, db: Session = Depends(get_db)):
    reply = db.query(Reply).filter(Reply.id == reply_id).first()
    if reply and reply.follow_up_status == "pending":
        reply.follow_up_status = "skipped"
        db.commit()
        db.refresh(reply)

    # If called from chat page, redirect back
    form = await request.form()
    redirect_url = form.get("redirect")
    if redirect_url:
        return RedirectResponse(url=redirect_url, status_code=303)

    thread = _get_thread(reply.message_id, db)
    return templates.TemplateResponse(request, "partials/thread_card.html", {"thread": thread})




@router.post("/messages/{message_id}/reply")
async def send_manual_reply(request: Request, message_id: int, db: Session = Depends(get_db)):
    """Send a free-form reply from the chat page (for concluded/waiting threads)."""
    form = await request.form()
    body = form.get("body", "").strip()
    redirect_url = form.get("redirect")

    if body:
        message = db.query(Message).filter(Message.id == message_id).first()
        thread = db.query(Reply).filter(Reply.message_id == message_id).order_by(Reply.round_number).all()
        current_round = max(r.round_number for r in thread) if thread else 0

        # Save outbound reply
        outbound = Reply(
            message_id=message_id,
            body=body,
            sentiment="neutral",
            direction="outbound",
            round_number=current_round + 1,
            reply_at=datetime.utcnow(),
            follow_up_status="sent",
        )
        db.add(outbound)
        db.commit()

        # Generate a response from the contact
        from app.services.inbox import generate_synthetic_reply, suggest_follow_up, _build_thread_history
        profile = message.profile or db.query(Profile).filter(Profile.id == message.profile_id).first()
        goal = message.goal or db.query(Goal).filter(Goal.id == message.goal_id).first()

        all_replies = db.query(Reply).filter(Reply.message_id == message_id).order_by(Reply.round_number).all()
        history = _build_thread_history(all_replies, message.body)
        last_inbound = [r for r in all_replies if r.direction == "inbound"]
        prev_sentiment = last_inbound[-1].sentiment if last_inbound else "neutral"

        try:
            import time
            from app.config import settings
            time.sleep(settings.GROQ_RATE_LIMIT_DELAY)
            result = generate_synthetic_reply(
                message, profile, history, round_number=current_round + 2, prev_sentiment=prev_sentiment,
            )
            time.sleep(settings.GROQ_RATE_LIMIT_DELAY)
            updated_history = history + f"\n[THEM]\n{result['body']}\n"
            follow_up = ""
            if not result["is_conclusion"] or result["sentiment"] == "positive":
                follow_up = suggest_follow_up(
                    updated_history, result["sentiment"], profile, goal, result["is_conclusion"],
                )
            new_reply = Reply(
                message_id=message_id,
                body=result["body"],
                sentiment=result["sentiment"],
                direction="inbound",
                round_number=current_round + 2,
                is_conclusion=result["is_conclusion"],
                reply_at=result["reply_at"],
                follow_up_suggestion=follow_up,
            )
            db.add(new_reply)
            db.commit()
        except Exception:
            pass

    if redirect_url:
        return RedirectResponse(url=redirect_url, status_code=303)
    return RedirectResponse(url="/", status_code=303)


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
