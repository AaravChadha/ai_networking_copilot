import json
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.orm import relationship

from app.database import Base


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    company = Column(String, nullable=False)
    education = Column(String, default="")
    skills = Column(Text, default="[]")  # JSON array
    career_tags = Column(Text, default="[]")  # JSON array
    location = Column(String, default="")
    seniority = Column(String, default="mid")  # intern/junior/mid/senior/exec
    linkedin_url = Column(String, default="")

    def get_skills(self) -> list[str]:
        return json.loads(self.skills)

    def get_career_tags(self) -> list[str]:
        return json.loads(self.career_tags)


class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True)
    goal_type = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    user_background = Column(Text, default="")
    target_roles = Column(Text, default="[]")  # JSON array
    target_companies = Column(Text, default="[]")  # JSON array
    status = Column(String, default="active")  # active/paused/completed
    created_at = Column(DateTime, default=datetime.utcnow)

    messages = relationship("Message", back_populates="goal")
    send_config = relationship("SendConfig", back_populates="goal", uselist=False)

    def get_target_roles(self) -> list[str]:
        return json.loads(self.target_roles)

    def get_target_companies(self) -> list[str]:
        return json.loads(self.target_companies)


class OutreachTemplate(Base):
    __tablename__ = "outreach_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    template_type = Column(String, nullable=False)
    tone = Column(String, default="professional")
    intro_template = Column(Text, default="")
    context_template = Column(Text, default="")
    ask_template = Column(Text, default="")
    closing_template = Column(Text, default="")
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=True)


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=False)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("outreach_templates.id"), nullable=True)
    subject = Column(String, default="")
    body = Column(Text, default="")
    status = Column(String, default="draft")  # draft/approved/sent/replied
    mode = Column(String, default="manual")  # manual/automatic
    priority_score = Column(Float, default=0.0)
    scheduled_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    goal = relationship("Goal", back_populates="messages")
    profile = relationship("Profile")
    replies = relationship("Reply", back_populates="message")


class Reply(Base):
    __tablename__ = "replies"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    body = Column(Text, default="")
    sentiment = Column(String, default="neutral")  # positive/neutral/negative
    reply_at = Column(DateTime, default=datetime.utcnow)
    follow_up_suggestion = Column(Text, default="")
    follow_up_status = Column(String, default="pending")  # pending/sent/skipped

    message = relationship("Message", back_populates="replies")


class SendConfig(Base):
    __tablename__ = "send_config"

    id = Column(Integer, primary_key=True, index=True)
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=False)
    max_per_day = Column(Integer, default=10)
    warmup_enabled = Column(Boolean, default=False)
    warmup_start = Column(Integer, default=3)
    warmup_increment = Column(Integer, default=2)
    is_paused = Column(Boolean, default=False)
    schedule_start_hour = Column(Integer, default=9)
    schedule_end_hour = Column(Integer, default=17)

    goal = relationship("Goal", back_populates="send_config")
