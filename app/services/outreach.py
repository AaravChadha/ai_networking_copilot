import time

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Goal, Message, OutreachTemplate, Profile
from app.services.groq_client import chat


def generate_message(
    goal: Goal,
    profile: Profile,
    template: OutreachTemplate,
    tone: str = "professional",
    intro_override: str = "",
    context_override: str = "",
    ask_override: str = "",
    closing_override: str = "",
) -> dict:
    """Generate a personalized outreach message for a single contact."""
    intro_inst = intro_override or template.intro_template
    context_inst = context_override or template.context_template
    ask_inst = ask_override or template.ask_template
    closing_inst = closing_override or template.closing_template

    system_prompt = f"""You are a skilled networking message writer. Write a personalized outreach message that feels genuinely human — like someone who actually took the time to learn about the recipient.

CRITICAL RULES:
- Write in first person as the sender
- Reference SPECIFIC details about the recipient (their role, company, skills, projects)
- NO generic phrases like "I came across your profile" or "I hope this finds you well"
- NO buzzwords or corporate speak
- Keep it under 150 words total
- Make it sound like a real person wrote this, not a template
- Tone: {tone}

The message must have 4 sections that flow naturally as one cohesive message (do NOT label the sections):

1. INTRODUCTION: {intro_inst}
2. CONTEXT: {context_inst}
3. THE ASK: {ask_inst}
4. CLOSING: {closing_inst}"""

    user_prompt = f"""SENDER INFO:
- Goal: {goal.goal_type}
- Description: {goal.description}
- Background: {goal.user_background}

RECIPIENT INFO:
- Name: {profile.name}
- Role: {profile.role}
- Company: {profile.company}
- Seniority: {profile.seniority}
- Skills: {', '.join(profile.get_skills())}
- Education: {profile.education}
- Location: {profile.location}

Write the outreach message now. Also generate a short, specific subject line (under 10 words) that would make them want to open this message. Format your response as:

SUBJECT: <subject line>

<message body>"""

    response = chat(system_prompt, user_prompt)

    # Parse subject and body
    subject = ""
    body = response
    if "SUBJECT:" in response:
        parts = response.split("\n", 1)
        for i, line in enumerate(response.split("\n")):
            if line.strip().startswith("SUBJECT:"):
                subject = line.replace("SUBJECT:", "").strip()
                body = "\n".join(response.split("\n")[i + 1:]).strip()
                break

    return {"subject": subject, "body": body}


def batch_generate(
    goal: Goal,
    profile_ids: list[int],
    template: OutreachTemplate,
    tone: str,
    intro_override: str,
    context_override: str,
    ask_override: str,
    closing_override: str,
    db: Session,
) -> list[Message]:
    """Generate messages for multiple contacts with rate limiting."""
    profiles = db.query(Profile).filter(Profile.id.in_(profile_ids)).all()
    messages = []

    for i, profile in enumerate(profiles):
        if i > 0:
            time.sleep(settings.GROQ_RATE_LIMIT_DELAY)

        try:
            result = generate_message(
                goal, profile, template, tone,
                intro_override, context_override, ask_override, closing_override,
            )
        except Exception:
            result = {
                "subject": f"Reaching out — {goal.goal_type}",
                "body": f"Hi {profile.name},\n\n[Message generation failed. Please edit this draft manually.]\n\nBest regards",
            }

        msg = Message(
            goal_id=goal.id,
            profile_id=profile.id,
            template_id=template.id,
            subject=result["subject"],
            body=result["body"],
            status="draft",
            priority_score=0.0,
        )
        db.add(msg)
        messages.append(msg)

    db.commit()
    for m in messages:
        db.refresh(m)

    return messages
