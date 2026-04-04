import random
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import Message, Profile, Reply
from app.services.groq_client import chat


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
