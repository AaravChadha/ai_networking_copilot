from datetime import datetime

from pydantic import BaseModel


# --- Goals ---

class GoalCreate(BaseModel):
    goal_type: str
    description: str
    user_background: str = ""
    target_roles: list[str] = []
    target_companies: list[str] = []


class GoalResponse(BaseModel):
    id: int
    goal_type: str
    description: str
    user_background: str
    target_roles: list[str]
    target_companies: list[str]
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Profiles ---

class ProfileResponse(BaseModel):
    id: int
    name: str
    role: str
    company: str
    education: str
    skills: list[str]
    career_tags: list[str]
    location: str
    seniority: str
    linkedin_url: str

    model_config = {"from_attributes": True}


class RankedProfile(BaseModel):
    profile: ProfileResponse
    score: float
    reason: str


# --- Messages ---

class MessageCreate(BaseModel):
    profile_id: int
    template_id: int | None = None


class MessageUpdate(BaseModel):
    subject: str | None = None
    body: str | None = None
    mode: str | None = None


class MessageResponse(BaseModel):
    id: int
    goal_id: int
    profile_id: int
    template_id: int | None
    subject: str
    body: str
    status: str
    mode: str
    priority_score: float
    sent_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Templates ---

class TemplateCreate(BaseModel):
    name: str
    template_type: str
    tone: str = "professional"
    intro_template: str = ""
    context_template: str = ""
    ask_template: str = ""
    closing_template: str = ""
    goal_id: int | None = None


class TemplateResponse(BaseModel):
    id: int
    name: str
    template_type: str
    tone: str
    intro_template: str
    context_template: str
    ask_template: str
    closing_template: str
    goal_id: int | None

    model_config = {"from_attributes": True}


# --- Replies ---

class ReplyResponse(BaseModel):
    id: int
    message_id: int
    body: str
    sentiment: str
    reply_at: datetime
    follow_up_suggestion: str
    follow_up_status: str

    model_config = {"from_attributes": True}


# --- Send Config ---

class SendConfigUpdate(BaseModel):
    max_per_day: int | None = None
    warmup_enabled: bool | None = None
    warmup_start: int | None = None
    warmup_increment: int | None = None
    is_paused: bool | None = None
    schedule_start_hour: int | None = None
    schedule_end_hour: int | None = None


# --- Generation Requests ---

class GenerateMessagesRequest(BaseModel):
    profile_ids: list[int]
    template_id: int
