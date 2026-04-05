import json
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import FastAPI
from app.config import BASE_DIR
from app.database import SessionLocal, create_tables
from app.models import Goal, Message, Profile, Reply, SendConfig


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    _migrate_goal_title()
    seed_profiles()
    seed_templates()
    seed_demo_data()
    yield


def _migrate_goal_title():
    """Add title column if missing, backfill empty titles."""
    from sqlalchemy import text, inspect
    db = SessionLocal()
    try:
        inspector = inspect(db.bind)
        cols = [c["name"] for c in inspector.get_columns("goals")]
        if "title" not in cols:
            db.execute(text("ALTER TABLE goals ADD COLUMN title VARCHAR DEFAULT ''"))
            db.commit()
        # Backfill goals with no title
        goals = db.query(Goal).filter((Goal.title == None) | (Goal.title == "")).all()
        if goals:
            from app.services.groq_client import chat
            for g in goals:
                try:
                    t = chat(
                        "Generate a short 3-5 word campaign title from the user's networking goal. Return ONLY the title, nothing else. Capitalize it like a proper title.",
                        f"Goal type: {g.goal_type}\nDescription: {g.description}",
                        temperature=0.3,
                    ).strip().strip('"').strip("'")
                    g.title = t
                except Exception:
                    g.title = g.description[:50]
            db.commit()
    finally:
        db.close()


def seed_profiles():
    db = SessionLocal()
    try:
        if db.query(Profile).count() == 0:
            seed_file = BASE_DIR / "data" / "seed_profiles.json"
            if seed_file.exists():
                profiles = json.loads(seed_file.read_text())
                for p in profiles:
                    db.add(Profile(
                        name=p["name"],
                        role=p["role"],
                        company=p["company"],
                        education=p.get("education", ""),
                        skills=json.dumps(p.get("skills", [])),
                        career_tags=json.dumps(p.get("career_tags", [])),
                        location=p.get("location", ""),
                        seniority=p.get("seniority", "mid"),
                        linkedin_url=p.get("linkedin_url", ""),
                    ))
                db.commit()
    finally:
        db.close()


def seed_templates():
    from app.services.templates import seed_default_templates
    db = SessionLocal()
    try:
        seed_default_templates(db)
    finally:
        db.close()


def seed_demo_data():
    """Seed a sample campaign with messages and replies for demo purposes."""
    db = SessionLocal()
    try:
        if db.query(Goal).count() > 0:
            return

        # Need at least 3 profiles
        profiles = db.query(Profile).limit(5).all()
        if len(profiles) < 3:
            return

        goal = Goal(
            goal_type="internship",
            description="ML/AI internship at a top tech company",
            user_background="CS junior at Purdue, experience with PyTorch and NLP research",
            target_roles=json.dumps(["ML Engineer", "AI Researcher", "Data Scientist"]),
            target_companies=json.dumps(["Google", "Meta", "OpenAI"]),
            status="active",
        )
        db.add(goal)
        db.commit()
        db.refresh(goal)

        db.add(SendConfig(goal_id=goal.id))
        db.commit()

        demo_convos = [
            {
                "profile_idx": 0,
                "subject": "Your ML work caught my eye",
                "body": f"Hi {profiles[0].name},\n\nI noticed your work on machine learning at {profiles[0].company}. As a CS junior at Purdue doing NLP research, I'd love to hear about your experience and any advice for breaking into ML roles.\n\nWould you have 15 minutes for a quick chat?",
                "status": "sent",
                "replies": [
                    {"body": f"Hi! Thanks for reaching out. I'd be happy to chat about ML careers. I remember being in your shoes not too long ago. How about next Tuesday afternoon?", "sentiment": "positive", "direction": "inbound", "round": 1, "follow_up_status": "sent", "follow_up_suggestion": "That works perfectly! I'm free Tuesday 2-4pm. Should I send a calendar invite?"},
                    {"body": "That works perfectly! I'm free Tuesday 2-4pm. Should I send a calendar invite?", "sentiment": "", "direction": "outbound", "round": 2, "follow_up_status": "pending", "follow_up_suggestion": ""},
                    {"body": "Sure, send it to my work email. Looking forward to it! Also feel free to bring any specific questions about our team's work on recommendation systems.", "sentiment": "positive", "direction": "inbound", "round": 3, "follow_up_status": "pending", "follow_up_suggestion": "Thanks so much! I'll send the invite now. I'd love to hear about the recommendation systems work — I've been exploring similar architectures in my research. See you Tuesday!"},
                ],
            },
            {
                "profile_idx": 1,
                "subject": f"Quick question about {profiles[1].company}",
                "body": f"Hi {profiles[1].name},\n\nI'm a CS student at Purdue researching ML internship opportunities. Your background in {profiles[1].role} at {profiles[1].company} is exactly the kind of role I'm targeting.\n\nWould you mind sharing what the interview process was like?",
                "status": "sent",
                "replies": [
                    {"body": "Thanks for the message. I'm pretty swamped right now but I can point you to our careers page — we have a great internship program. Apply through there and mention my name if you'd like.", "sentiment": "neutral", "direction": "inbound", "round": 1, "follow_up_status": "pending", "follow_up_suggestion": "I really appreciate the pointer! I'll apply through the careers page and mention your name. Thanks for taking the time to respond."},
                ],
            },
            {
                "profile_idx": 2,
                "subject": f"Admire your path at {profiles[2].company}",
                "body": f"Hi {profiles[2].name},\n\nYour career trajectory from research to {profiles[2].role} at {profiles[2].company} is inspiring. I'm exploring similar paths and would value any insights you could share.\n\nBest regards",
                "status": "sent",
                "replies": [
                    {"body": "I appreciate the kind words but I'm not really taking informational interviews right now. Best of luck with your search though!", "sentiment": "negative", "direction": "inbound", "round": 1, "is_conclusion": True, "follow_up_status": "pending", "follow_up_suggestion": "Completely understand — thanks for letting me know and for the well wishes. Best of luck with everything at " + profiles[2].company + "!"},
                ],
            },
        ]

        now = datetime.utcnow()
        for i, convo in enumerate(demo_convos):
            p = profiles[convo["profile_idx"]]
            msg = Message(
                goal_id=goal.id,
                profile_id=p.id,
                subject=convo["subject"],
                body=convo["body"],
                status=convo["status"],
                priority_score=0.9 - i * 0.1,
                sent_at=now - timedelta(days=3 - i),
                created_at=now - timedelta(days=4 - i),
            )
            db.add(msg)
            db.commit()
            db.refresh(msg)

            for r in convo["replies"]:
                reply = Reply(
                    message_id=msg.id,
                    body=r["body"],
                    sentiment=r.get("sentiment", ""),
                    direction=r["direction"],
                    round_number=r["round"],
                    is_conclusion=r.get("is_conclusion", False),
                    reply_at=now - timedelta(days=2 - i, hours=r["round"]),
                    follow_up_suggestion=r.get("follow_up_suggestion", ""),
                    follow_up_status=r.get("follow_up_status", "pending"),
                )
                db.add(reply)

            if convo["status"] == "sent":
                msg.status = "replied"

        db.commit()
    finally:
        db.close()


app = FastAPI(title="AI Networking Copilot", lifespan=lifespan)

from app.routers import pages, goals, contacts, messages, inbox  # noqa: E402

app.include_router(pages.router)
app.include_router(goals.router)
app.include_router(contacts.router)
app.include_router(messages.router)
app.include_router(inbox.router)
