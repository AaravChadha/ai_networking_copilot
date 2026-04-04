from sqlalchemy.orm import Session

from app.models import OutreachTemplate

DEFAULT_TEMPLATES = [
    {
        "name": "Informational Interview",
        "template_type": "informational",
        "tone": "professional",
        "intro_template": "Write a warm, genuine opening. Mention how you found them or why they caught your eye. Reference something specific about their background — a project, role transition, or shared interest. Do NOT use generic phrases like 'I came across your profile.'",
        "context_template": "Briefly share who you are and what you're working on. Connect your background to theirs — find a genuine overlap in interests, skills, or experience. Keep it personal, not resume-like.",
        "ask_template": "Ask for a short informational chat (15-20 min). Be specific about what you'd love to learn from them — mention a topic related to their expertise. Make it easy to say yes.",
        "closing_template": "End warmly and respectfully. Acknowledge they're busy. Leave the door open without being pushy. No forced enthusiasm.",
    },
    {
        "name": "Internship / Job Inquiry",
        "template_type": "job",
        "tone": "professional",
        "intro_template": "Open with a specific reason you're excited about their company or team. Reference a recent project, product, or initiative they're involved in. Show you've done your homework.",
        "context_template": "Share your relevant experience concisely. Highlight 1-2 specific projects or skills that align with their work. Draw a clear line between what you've done and what their team does.",
        "ask_template": "Ask if they'd be open to sharing advice about opportunities on their team, or if they could point you to the right person. Don't directly ask for a job — ask for guidance.",
        "closing_template": "Thank them genuinely. Mention you'd be happy to share your work or portfolio if they're interested. Keep it confident but not presumptuous.",
    },
    {
        "name": "Research Collaboration",
        "template_type": "research",
        "tone": "professional",
        "intro_template": "Reference their specific research work — a paper, talk, or project. Explain what about it resonated with you and why. Show genuine intellectual curiosity, not flattery.",
        "context_template": "Describe your own research interests and current work. Highlight where your work intersects or complements theirs. Be specific about methods, domains, or problems you're both tackling.",
        "ask_template": "Propose a concrete idea for collaboration or ask if they'd be open to discussing potential overlap. Suggest a specific topic you'd love to explore together.",
        "closing_template": "Express enthusiasm for their work genuinely. Offer to share your own papers or results. Keep the academic tone but stay human.",
    },
    {
        "name": "Investor Outreach",
        "template_type": "investor",
        "tone": "professional",
        "intro_template": "Lead with a compelling hook about the problem you're solving. Reference the investor's portfolio or thesis to show why they specifically would care. Make the first line impossible to ignore.",
        "context_template": "Share traction, key metrics, or a concrete milestone. Keep it brief — 2-3 sentences max. Show momentum, not just an idea. Reference your team's relevant expertise.",
        "ask_template": "Ask for a short meeting to share more details. Be direct about what stage you're at and what you're looking for. Don't be vague — investors appreciate clarity.",
        "closing_template": "End with confidence. Mention one more compelling detail (a customer, a metric, a milestone). Make them want to learn more.",
    },
    {
        "name": "Custom",
        "template_type": "custom",
        "tone": "friendly",
        "intro_template": "Write a natural, personalized opening based on the recipient's background. Find a genuine reason to reach out — shared interests, mutual connections, or something you admire about their work.",
        "context_template": "Share relevant context about yourself. Be authentic and concise. Explain what you're working on and why it connects to them.",
        "ask_template": "Make a clear, specific ask. Whether it's advice, a chat, or feedback — be direct about what you'd appreciate from them.",
        "closing_template": "Close naturally. Be genuine and respectful of their time. No clichés.",
    },
]


def seed_default_templates(db: Session):
    """Seed default outreach templates if none exist."""
    if db.query(OutreachTemplate).count() > 0:
        return

    for t in DEFAULT_TEMPLATES:
        db.add(OutreachTemplate(**t))
    db.commit()


def get_templates(db: Session, goal_id: int | None = None) -> list[OutreachTemplate]:
    """Get all templates, including any custom ones for a specific goal."""
    query = db.query(OutreachTemplate).filter(
        (OutreachTemplate.goal_id == None) | (OutreachTemplate.goal_id == goal_id)  # noqa: E711
    )
    return query.all()
