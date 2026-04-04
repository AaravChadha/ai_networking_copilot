# AI Networking Copilot

An AI-powered networking copilot that automates the entire professional outreach pipeline — from defining career goals to discovering relevant contacts, generating personalized messages, and managing conversations with AI-driven follow-ups.

Built solo at **Catapult Hacks** (Purdue University) in 36 hours. Budget: **$0** — everything runs on free tiers.

## Screenshots

<!-- Add screenshots here -->

## What It Does

1. **Define your goal** — Tell the AI what you're looking for (internship, mentorship, research collab, etc.) and your background
2. **Discover contacts** — AI prefilters 500 professionals down to ~50, then ranks them with match scores and reasons in a single LLM call
3. **Generate outreach** — Pick from 5 built-in templates (informational interview, job inquiry, research collab, investor outreach, custom), set the tone, and AI writes personalized messages referencing each contact's specific role, skills, and company
4. **Send and track** — Approve, edit inline, and send messages with batch controls
5. **Manage conversations** — Multi-round back-and-forth in a WhatsApp-style chat interface with AI-generated replies, sentiment classification (positive/neutral/negative), and context-aware follow-up suggestions that adapt to conversation tone
6. **Dashboard analytics** — Track campaign performance with reply rates, sentiment doughnut charts, messages-per-campaign bar charts, and per-campaign breakdowns

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Backend | FastAPI | Async, serves both API + HTML in one process |
| Frontend | Jinja2 + HTMX + Pico CSS | No JS framework, no build step, server-rendered |
| Database | SQLite + SQLAlchemy | Zero config, file-based |
| LLM | Groq (Llama 3.3 70B) | Free tier, fast inference, JSON mode |
| Charts | Chart.js | Lightweight, CDN-loaded |

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

## Built By

**Aarav Chadha** — Catapult Hacks, Purdue University
