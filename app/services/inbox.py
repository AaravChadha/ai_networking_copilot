import random
import time
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Goal, Message, Profile, Reply
from app.services.groq_client import chat, chat_json


def _build_thread_history(replies: list[Reply], original_message: str) -> str:
    """Build a formatted conversation history from a thread of replies."""
    history = f"[ORIGINAL OUTREACH]\n{original_message}\n"
    for r in sorted(replies, key=lambda x: x.round_number):
        label = "[THEM]" if r.direction == "inbound" else "[YOU]"
        history += f"\n{label}\n{r.body}\n"
    return history


def generate_synthetic_reply(message: Message, profile: Profile, conversation_history: str = "", round_number: int = 1, prev_sentiment: str = "") -> dict:
    """Generate a realistic synthetic reply to an outreach message via Groq.

    For round 1: sentiment is random (40% pos, 35% neutral, 25% neg).
    For later rounds: sentiment evolves toward a conclusion.
    """
    if round_number == 1:
        sentiment = random.choices(
            ["positive", "neutral", "negative"],
            weights=[40, 35, 25],
            k=1,
        )[0]
    else:
        # Sentiment evolution — conversations should progress
        if prev_sentiment == "positive":
            sentiment = random.choices(["positive", "neutral"], weights=[85, 15], k=1)[0]
        elif prev_sentiment == "neutral":
            sentiment = random.choices(["positive", "neutral", "negative"], weights=[50, 30, 20], k=1)[0]
        else:
            sentiment = "negative"

    # Determine if this should be the concluding message
    is_conclusion = False
    if round_number >= 3:
        is_conclusion = True
    elif round_number == 2 and sentiment == "negative":
        is_conclusion = True
    elif round_number == 2 and sentiment == "positive" and random.random() > 0.5:
        is_conclusion = True

    conclusion_guidance = {
        "positive": "This is your FINAL reply. Commit to a concrete next step: confirm a meeting time, agree to a call, or offer to make an introduction. Make it clear the conversation has reached a positive resolution.",
        "neutral": "This is your FINAL reply. Politely close the conversation — say you'll keep them in mind, or suggest reconnecting in the future. Be kind but make it clear this is wrapping up.",
        "negative": "This is your FINAL reply. Decline clearly but graciously. Wish them well. End the conversation definitively.",
    }

    tone_guidance = {
        "positive": "Reply warmly and show genuine interest. Accept the request or suggest a next step (e.g., schedule a call, share a resource). Be encouraging but realistic.",
        "neutral": "Reply politely but non-committally. Show mild interest but don't commit to anything specific. Maybe ask for more info or say you're busy right now.",
        "negative": "Reply briefly and decline. Be professional but clearly not interested. Maybe say you're too busy, not the right person, or not taking meetings.",
    }

    guidance = conclusion_guidance[sentiment] if is_conclusion else tone_guidance[sentiment]

    system_prompt = f"""You are {profile.name}, a {profile.seniority} {profile.role} at {profile.company}. You are in an ongoing email conversation. Write your next reply.

RULES:
- Write as {profile.name} in first person
- Keep it under 80 words
- Sound like a real person — natural, not robotic
- {guidance}
- Do NOT include a subject line or email headers
- Just write the reply body"""

    if conversation_history:
        user_prompt = f"""CONVERSATION SO FAR:
{conversation_history}

Write your next reply."""
    else:
        user_prompt = f"""The message you received:

Subject: {message.subject}

{message.body}

Write your reply now."""

    body = chat(system_prompt, user_prompt, temperature=0.8)

    delay_hours = random.randint(4, 48) if round_number > 1 else random.randint(12, 72)
    reply_at = datetime.utcnow() + timedelta(hours=delay_hours)

    return {
        "body": body.strip(),
        "sentiment": sentiment,
        "reply_at": reply_at,
        "is_conclusion": is_conclusion,
    }


def classify_reply(reply_body: str, original_message: str) -> dict:
    """Classify a reply's sentiment and extract key signal phrases via Groq JSON mode."""
    system_prompt = """You are an email reply analyst. Classify the sentiment of a reply to a networking outreach message and extract key signal phrases.

Return JSON with exactly this structure:
{
  "sentiment": "positive" | "neutral" | "negative",
  "signals": ["signal phrase 1", "signal phrase 2", ...]
}

Signals are short phrases (3-8 words) that indicate the recipient's intent. Examples:
- Positive: "happy to chat", "let's schedule a call", "I'd love to help"
- Neutral: "let me think about it", "send me more details", "busy right now"
- Negative: "not interested", "not the right fit", "too busy to meet"

Return 2-4 signal phrases."""

    user_prompt = f"""ORIGINAL OUTREACH MESSAGE:
{original_message}

REPLY RECEIVED:
{reply_body}

Classify this reply."""

    result = chat_json(system_prompt, user_prompt)

    sentiment = result.get("sentiment", "neutral")
    if sentiment not in ("positive", "neutral", "negative"):
        sentiment = "neutral"
    signals = result.get("signals", [])

    return {"sentiment": sentiment, "signals": signals}


def suggest_follow_up(
    conversation_history: str,
    sentiment: str,
    profile: Profile,
    goal: Goal,
    is_conclusion: bool = False,
) -> str:
    """Generate a context-aware follow-up suggestion based on conversation history."""
    if is_conclusion and sentiment == "negative":
        # No follow-up needed for concluded negative conversations
        return ""

    if is_conclusion and sentiment == "positive":
        guidance = "They've agreed to connect! Write a brief, warm confirmation. Confirm the next step they mentioned (meeting, call, etc.), thank them, and express excitement. Keep it short — this wraps up the conversation."
    elif is_conclusion:
        guidance = "The conversation is wrapping up. Write a graceful closing — thank them for their time and leave the door open for the future. Keep it brief."
    else:
        sentiment_guidance = {
            "positive": "They're interested! Suggest a concrete next step — propose a specific meeting time, offer to share relevant work, or ask a focused follow-up question. Be enthusiastic but not pushy.",
            "neutral": "They're on the fence. Provide additional context that might tip them toward interest — mention a specific shared connection, relevant achievement, or lower the ask. Keep it light.",
            "negative": "They declined. Write a graceful, brief close — thank them for their time, ask if there's someone else they'd recommend, or leave the door open for the future. Do NOT be pushy.",
        }
        guidance = sentiment_guidance.get(sentiment, sentiment_guidance["neutral"])

    system_prompt = f"""You are a networking coach. Based on an ongoing conversation, write the next follow-up message.

RULES:
- Write as the original sender in first person
- Keep it under 80 words
- {guidance}
- Sound natural and human
- Do NOT include a subject line
- Just write the follow-up body"""

    user_prompt = f"""SENDER'S GOAL: {goal.goal_type} — {goal.description}
SENDER'S BACKGROUND: {goal.user_background}

RECIPIENT: {profile.name}, {profile.role} at {profile.company}

CONVERSATION SO FAR:
{conversation_history}

Write the follow-up message."""

    return chat(system_prompt, user_prompt, temperature=0.7).strip()


def continue_conversation(reply_id: int, follow_up_body: str, db: Session) -> Reply | None:
    """Send a follow-up and generate the next reply in the conversation.

    Returns the new inbound Reply, or None if the conversation has concluded.
    """
    reply = db.query(Reply).filter(Reply.id == reply_id).first()
    if not reply:
        return None

    message = reply.message
    profile = message.profile or db.query(Profile).filter(Profile.id == message.profile_id).first()
    goal = message.goal or db.query(Goal).filter(Goal.id == message.goal_id).first()

    # Get current thread
    thread = db.query(Reply).filter(Reply.message_id == message.id).order_by(Reply.round_number).all()
    current_round = max(r.round_number for r in thread) if thread else 1

    # Save the outbound follow-up
    outbound = Reply(
        message_id=message.id,
        body=follow_up_body,
        sentiment=reply.sentiment,
        direction="outbound",
        round_number=current_round + 1,
        reply_at=datetime.utcnow(),
        follow_up_status="sent",
    )
    db.add(outbound)
    reply.follow_up_status = "sent"
    db.commit()
    db.refresh(outbound)

    # Check if the last inbound was a conclusion — no more replies
    if reply.is_conclusion and reply.sentiment == "negative":
        return None

    # Determine if they reply to this follow-up
    # Decreasing probability: round 2 → 80%, round 3 → 60%, round 4+ → 30%
    reply_chance = {2: 0.8, 3: 0.6}.get(current_round + 1, 0.3)
    if reply.is_conclusion:
        # If previous was a positive/neutral conclusion, small chance of one more
        reply_chance = 0.3

    if random.random() > reply_chance:
        return None

    # Build conversation history
    all_replies = db.query(Reply).filter(Reply.message_id == message.id).order_by(Reply.round_number).all()
    history = _build_thread_history(all_replies, message.body)

    # Get the last inbound sentiment for evolution
    last_inbound = [r for r in all_replies if r.direction == "inbound"]
    prev_sentiment = last_inbound[-1].sentiment if last_inbound else "neutral"

    time.sleep(settings.GROQ_RATE_LIMIT_DELAY)

    try:
        new_round = current_round + 2
        result = generate_synthetic_reply(
            message, profile, history, round_number=new_round, prev_sentiment=prev_sentiment,
        )

        # Generate follow-up suggestion for the new reply
        time.sleep(settings.GROQ_RATE_LIMIT_DELAY)
        updated_history = history + f"\n[THEM]\n{result['body']}\n"

        follow_up = ""
        if not result["is_conclusion"] or result["sentiment"] == "positive":
            follow_up = suggest_follow_up(
                updated_history, result["sentiment"], profile, goal, result["is_conclusion"],
            )

        new_reply = Reply(
            message_id=message.id,
            body=result["body"],
            sentiment=result["sentiment"],
            direction="inbound",
            round_number=new_round,
            is_conclusion=result["is_conclusion"],
            reply_at=result["reply_at"],
            follow_up_suggestion=follow_up,
        )
        db.add(new_reply)
        db.commit()
        db.refresh(new_reply)
        return new_reply
    except Exception:
        return None


def generate_replies_for_sent(messages: list[Message], db: Session) -> list[Reply]:
    """Generate synthetic replies for a list of sent messages.

    ~60-80% of messages get replies. For demo mode, replies are generated
    immediately but have future timestamps to simulate realistic delays.
    """
    reply_rate = random.uniform(0.6, 0.8)
    replies = []

    for i, msg in enumerate(messages):
        if msg.status != "sent":
            continue
        if random.random() > reply_rate:
            continue

        profile = msg.profile
        if not profile:
            profile = db.query(Profile).filter(Profile.id == msg.profile_id).first()

        if i > 0 and replies:
            time.sleep(settings.GROQ_RATE_LIMIT_DELAY)

        try:
            result = generate_synthetic_reply(msg, profile)

            time.sleep(settings.GROQ_RATE_LIMIT_DELAY)
            goal = msg.goal
            if not goal:
                goal = db.query(Goal).filter(Goal.id == msg.goal_id).first()

            history = f"[ORIGINAL OUTREACH]\n{msg.body}\n\n[THEM]\n{result['body']}\n"
            follow_up = suggest_follow_up(
                history, result["sentiment"], profile, goal, result.get("is_conclusion", False),
            )

            reply = Reply(
                message_id=msg.id,
                body=result["body"],
                sentiment=result["sentiment"],
                direction="inbound",
                round_number=1,
                is_conclusion=result.get("is_conclusion", False),
                reply_at=result["reply_at"],
                follow_up_suggestion=follow_up,
            )
            db.add(reply)
            msg.status = "replied"
            replies.append(reply)
        except Exception:
            continue

    if replies:
        db.commit()
        for r in replies:
            db.refresh(r)

    return replies
