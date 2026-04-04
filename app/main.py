import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from app.config import BASE_DIR
from app.database import SessionLocal, create_tables
from app.models import Profile


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    seed_profiles()
    seed_templates()
    yield


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


app = FastAPI(title="AI Networking Copilot", lifespan=lifespan)

from app.routers import pages, goals, contacts, messages  # noqa: E402

app.include_router(pages.router)
app.include_router(goals.router)
app.include_router(contacts.router)
app.include_router(messages.router)
