import random
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import Goal, Message, Profile, Reply
from app.services.groq_client import chat, chat_json


def generate_synthetic_reply(message: Message, profile: Profile) -> dict:
    """Generate a realistic synthetic reply to an outreach message via Groq.

    Returns dict with body and sentiment.
    Sentiment distribution: ~40% positive, 35% neutral, 25% negative.
    """
    # Decide sentiment with weighted random
    sentiment = random.choices(
        ["positive", "neutral", "negative"],
        weights=[40, 35, 25],
        k=1,
    )[0]

    tone_guidance = {
        "positive": "Reply warmly and show genuine interest. Accept the request or suggest a next step (e.g., schedule a call, share a resource). Be encouraging but realistic.",
        "neutral": "Reply politely but non-committally. Show mild interest but don't commit to anything specific. Maybe ask for more info or say you're busy right now.",
        "negative": "Reply briefly and decline. Be professional but clearly not interested. Maybe say you're too busy, not the right person, or not taking meetings.",
    }

    system_prompt = f"""You are {profile.name}, a {profile.seniority} {profile.role} at {profile.company}. Someone sent you a networking message. Write a realistic reply.

RULES:
- Write as {profile.name} in first person
- Keep it under 80 words
- Sound like a real person replying to an email — natural, not robotic
- {tone_guidance[sentiment]}
- Do NOT include a subject line
- Do NOT include email headers or signatures with full contact info
- Just write the reply body, starting with a greeting"""

    user_prompt = f"""The message you received:

Subject: {message.subject}

{message.body}

Write your reply now."""

    body = chat(system_prompt, user_prompt, temperature=0.8)

    # Simulate a reply arriving 1-3 days later
    delay_hours = random.randint(12, 72)
    reply_at = datetime.utcnow() + timedelta(hours=delay_hours)

    return {
        "body": body.strip(),
        "sentiment": sentiment,
        "reply_at": reply_at,
    }


def classify_reply(reply_body: str, original_message: str) -> dict:
    """Classify a reply's sentiment and extract key signal phrases via Groq JSON mode.

    Returns dict with sentiment (positive/neutral/negative) and signals (list of key phrases).
    """
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
    reply_body: str,
    original_message: str,
    sentiment: str,
    profile: Profile,
    goal: Goal,
) -> str:
    """Generate a context-aware follow-up suggestion based on the reply sentiment via Groq."""
    sentiment_guidance = {
        "positive": "They're interested! Suggest a concrete next step — propose a specific meeting time, offer to share relevant work, or ask a focused follow-up question. Be enthusiastic but not pushy.",
        "neutral": "They're on the fence. Provide additional context that might tip them toward interest — mention a specific shared connection, relevant achievement, or lower the ask. Keep it light.",
        "negative": "They declined. Write a graceful, brief close — thank them for their time, ask if there's someone else they'd recommend, or leave the door open for the future. Do NOT be pushy.",
    }

    system_prompt = f"""You are a networking coach. Based on a reply to an outreach message, write a follow-up message suggestion.

RULES:
- Write as the original sender in first person
- Keep it under 80 words
- {sentiment_guidance.get(sentiment, sentiment_guidance["neutral"])}
- Sound natural and human
- Do NOT include a subject line
- Just write the follow-up body"""

    user_prompt = f"""SENDER'S GOAL: {goal.goal_type} — {goal.description}
SENDER'S BACKGROUND: {goal.user_background}

RECIPIENT: {profile.name}, {profile.role} at {profile.company}

ORIGINAL OUTREACH:
{original_message}

THEIR REPLY ({sentiment}):
{reply_body}

Write the follow-up message."""

    return chat(system_prompt, user_prompt, temperature=0.7).strip()


def generate_replies_for_sent(messages: list[Message], db: Session) -> list[Reply]:
    """Generate synthetic replies for a list of sent messages.

    ~60-80% of messages get replies. For demo mode, replies are generated
    immediately but have future timestamps to simulate realistic delays.
    """
    import time
    from app.config import settings

    reply_rate = random.uniform(0.6, 0.8)
    replies = []

    for i, msg in enumerate(messages):
        if msg.status != "sent":
            continue
        # Skip some messages based on reply rate
        if random.random() > reply_rate:
            continue

        profile = msg.profile
        if not profile:
            profile = db.query(Profile).filter(Profile.id == msg.profile_id).first()

        # Rate limit between Groq calls
        if i > 0 and replies:
            time.sleep(settings.GROQ_RATE_LIMIT_DELAY)

        try:
            result = generate_synthetic_reply(msg, profile)
            reply = Reply(
                message_id=msg.id,
                body=result["body"],
                sentiment=result["sentiment"],
                reply_at=result["reply_at"],
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
