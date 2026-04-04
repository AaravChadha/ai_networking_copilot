# AI Networking Copilot

An AI-powered networking copilot that automates the entire professional outreach pipeline — from defining career goals to discovering relevant contacts, generating personalized messages, and managing conversations with AI-driven follow-ups.

Built solo at **Catapult Hacks** (Purdue University) in 36 hours.

---

## What It Does

1. **Define your goal** — Tell the AI what you're looking for (internship, mentorship, research collab, etc.) and your background
2. **Discover contacts** — AI ranks 500 synthetic professionals by relevance to your goal, with match scores and reasons
3. **Generate outreach** — Pick a template and tone; AI writes personalized messages for each contact using their specific role, skills, and company
4. **Send and track** — Approve, edit, and send messages with batch controls
5. **Manage conversations** — AI generates realistic replies, classifies sentiment, and suggests context-aware follow-ups in a WhatsApp-style chat interface
6. **Dashboard analytics** — Track campaign performance with reply rates, sentiment charts, and per-campaign breakdowns

## Screenshots

<!-- Add screenshots here -->

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Backend | FastAPI | Async, serves both API + HTML in one process |
| Frontend | Jinja2 + HTMX + Pico CSS | No JS framework, no build step, server-rendered |
| Database | SQLite + SQLAlchemy | Zero config, file-based |
| LLM | Groq (Llama 3.3 70B) | Free tier, fast inference, JSON mode |
| Charts | Chart.js | Lightweight, CDN-loaded |

**Budget: $0** — everything runs on free tiers.

## Features

- **Smart matching** — Prefilters 500 profiles down to ~50 candidates, then uses a single LLM call to rank and score them
- **Template system** — 5 built-in outreach templates (informational interview, job inquiry, research collab, investor outreach, custom) with customizable tone and sections
- **Personalized generation** — Each message references the recipient's specific role, company, skills, and background
- **Conversation threads** — Multi-round back-and-forth with AI-generated replies that evolve based on sentiment
- **Sentiment analysis** — Replies classified as positive/neutral/negative with signal extraction
- **Context-aware follow-ups** — AI suggests different follow-up strategies based on reply sentiment
- **WhatsApp-style chat** — Split-layout chat page with thread sidebar and message bubbles
- **Campaign navigation** — Breadcrumb flow: Contacts -> Templates -> Outreach -> Inbox
- **Dashboard charts** — Sentiment doughnut chart and messages-per-campaign bar chart
- **Demo-ready** — Seeds sample data on fresh start so the app is never empty

## Getting Started

**Requirements:** Python 3.11+, a free [Groq API key](https://console.groq.com/)

```bash
# Clone the repo
git clone https://github.com/AaravChadha/ai_networking_copilot.git
cd ai_networking_copilot

# Set up environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Add your Groq API key
echo "GROQ_API_KEY=your_key_here" > .env

# Run
python run.py
```

Open **http://localhost:8000** — the app seeds 500 synthetic profiles and demo data on first start.

> **Note:** To use this project, you must clone the repo and add your own Groq API key. There is no hosted version.

## How It Works

```
Dashboard → New Campaign → Goal Setup → Contacts (ranked) → Template Editor → Outreach (drafts) → Inbox (chat)
```

**6 distinct LLM call sites**, all routed through a single Groq client wrapper:

| Call | Purpose | Mode |
|------|---------|------|
| Profile ranking | Score and rank ~50 candidates against your goal | JSON |
| Message generation | Fill template with personalized content per contact | Text |
| Synthetic reply | Generate realistic responses (~40% pos, 35% neu, 25% neg) | Text |
| Reply classification | Classify sentiment + extract key signals | JSON |
| Follow-up suggestion | Context-aware follow-up based on conversation history | Text |
| Profile generation | One-time batch generation of 500 synthetic profiles | JSON |

## Project Structure

```
app/
├── main.py              # FastAPI app, startup hooks, demo data seeding
├── config.py            # Settings (API key, DB path)
├── database.py          # SQLite engine + session
├── models.py            # 6 SQLAlchemy ORM models
├── services/
│   ├── groq_client.py   # Groq SDK wrapper with retry
│   ├── matching.py      # Prefilter + AI ranking engine
��   ├── templates.py     # Outreach template CRUD
│   ├── outreach.py      # Message generation
│   └── inbox.py         # Replies, classification, follow-ups
├── routers/
│   ├── pages.py         # HTML page routes
│   ├── goals.py         # Goal CRUD + stats API
│   ├── contacts.py      # Contact search/rank API
│   ��── messages.py      # Message CRUD, approve, send API
│   └── inbox.py         # Reply/follow-up API
└── templates/           # Jinja2 HTML templates
    ├── base.html        # Layout with Pico CSS + HTMX
    ├── dashboard.html   # Stats, charts, campaign list
    ├── chat.html        # Split-layout conversation view
    └── ...
```

## Built By

**Aarav Chadha** — Catapult Hacks, Purdue University
