# AI Networking Copilot

## Project Overview
An AI-powered networking copilot that simulates professional networking workflows end-to-end. Users define career goals, discover relevant contacts from a synthetic professional network, generate structured personalized outreach, and manage responses in a controlled AI-driven pipeline.

**Type**: Hackathon project (36 hours)
**Budget**: $0 — all services must be free tier

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Backend | FastAPI | Async, fast, serves both API + HTML |
| Frontend | Jinja2 + HTMX + Pico CSS | No JS framework, no build step, one process |
| Database | SQLite + SQLAlchemy | Zero config, file-based, good enough for demo |
| LLM | Groq free tier (Llama 3.3 70B) | Free, fast inference, JSON mode support |
| Runtime | Python 3.11+ | Required for modern type hints + async |

### Key Libraries
```
fastapi, uvicorn[standard], jinja2, python-multipart,
sqlalchemy, groq, pydantic, python-dotenv
```

### Environment Variables
- `GROQ_API_KEY` — stored in `.env`, gitignored

---

## Project Structure

```
networking_ai/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app, startup hooks, router registration
│   ├── config.py                # Settings (GROQ_API_KEY, DB path, defaults)
│   ├── database.py              # SQLite engine, session, create_all()
│   ├── models.py                # SQLAlchemy ORM models
│   ├── schemas.py               # Pydantic request/response schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── groq_client.py       # Groq SDK wrapper, chat(), chat_json(), retry
│   │   ├── matching.py          # Prefilter + AI ranking engine
│   │   ├── templates.py         # Outreach template CRUD + defaults
│   │   ├── outreach.py          # Message generation via Groq
│   │   ├── inbox.py             # Synthetic replies, classification, follow-ups
│   │   └── scheduler.py         # Send queue, rate limits, warm-up logic
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── pages.py             # HTML page routes (Jinja2 rendered)
│   │   ├── goals.py             # Goal CRUD API
│   │   ├── contacts.py          # Contact search/rank API
│   │   ├── messages.py          # Message CRUD, approve, send API
│   │   └── inbox.py             # Inbox/reply/follow-up API
│   └── templates/               # Jinja2 HTML templates
│       ├── base.html            # Layout: nav, Pico CSS CDN, HTMX CDN
│       ├── dashboard.html       # Overview stats, active campaigns
│       ├── goal_setup.html      # Step 1: career goal + background form
│       ├── contacts.html        # Step 2: ranked contacts list
│       ├── template_editor.html # Step 3: pick/customize outreach template
│       ├── outreach.html        # Step 4: review/approve/send messages
│       ├── inbox.html           # Step 5: replies + follow-ups
│       └── partials/            # HTMX fragment templates
│           ├── contact_row.html
│           ├── message_card.html
│           └── reply_card.html
├── data/
│   └── seed_profiles.json       # Pre-generated 500 synthetic profiles
├── scripts/
│   └── generate_profiles.py     # One-shot Groq batch profile generator
├── requirements.txt
├── .env                         # GROQ_API_KEY (gitignored)
├── .gitignore
├── run.py                       # Entry point: uvicorn app.main:app
└── CLAUDE.md                    # This file
```

---

## Database Schema

### profiles (500 synthetic contacts)
- id (PK), name, role, company, education
- skills (JSON array), career_tags (JSON array)
- location, seniority (intern/junior/mid/senior/exec), linkedin_url

### goals
- id (PK), goal_type, description, user_background
- target_roles (JSON), target_companies (JSON)
- status (active/paused/completed), created_at

### outreach_templates
- id (PK), name, template_type, tone
- intro_template, context_template, ask_template, closing_template
- goal_id (FK → goals)

### messages
- id (PK), goal_id (FK), profile_id (FK), template_id (FK)
- subject, body, status (draft/approved/sent/replied)
- mode (manual/automatic), priority_score
- scheduled_at, sent_at, created_at

### replies
- id (PK), message_id (FK → messages)
- body, sentiment (positive/neutral/negative)
- reply_at, follow_up_suggestion, follow_up_status (pending/sent/skipped)

### send_config
- id (PK), goal_id (FK → goals)
- max_per_day, warmup_enabled, warmup_start, warmup_increment
- is_paused, schedule_start_hour, schedule_end_hour

---

## Groq LLM Integration

6 distinct LLM call sites — all go through `services/groq_client.py`:

| # | Call Site | Service | Mode | Purpose |
|---|----------|---------|------|---------|
| 1 | Profile Ranking | matching.py | JSON | Rank ~50 prefiltered candidates with scores + reasons |
| 2 | Message Generation | outreach.py | Text | Fill template variables with personalized content |
| 3 | Synthetic Reply | inbox.py | Text | Generate realistic reply (~40% pos, 35% neutral, 25% neg) |
| 4 | Reply Classification | inbox.py | JSON | Classify sentiment + extract key signals |
| 5 | Follow-up Suggestion | inbox.py | Text | Context-aware follow-up based on sentiment |
| 6 | Profile Generation | generate_profiles.py | JSON | 20 batches of 25 with diversity hints |

### Rate Limit Strategy
- Groq free tier: ~30 req/min, ~6000 tokens/min
- Batch profile ranking into single call (50 profiles in one prompt)
- 2s delay between sequential message generation calls
- Retry with exponential backoff on 429s
- Cache rankings in DB to avoid re-calling

---

## Web Pages & User Flow

```
Dashboard (/) → New Campaign → Goal Setup → Contacts → Template Editor → Outreach → Inbox
```

| Route | Page | Purpose |
|-------|------|---------|
| GET / | Dashboard | Stats, active campaigns, "New Campaign" CTA |
| GET /goals/new | Goal Setup | Form: goal type, description, background |
| GET /goals/{id}/contacts | Contacts | Ranked list with scores, checkboxes |
| GET /goals/{id}/templates | Template Editor | Pick type, set tone, preview |
| GET /goals/{id}/outreach | Outreach | Drafts, edit/approve, send controls |
| GET /goals/{id}/inbox | Inbox | Replies by sentiment, follow-up suggestions |

### HTMX Pattern
All dynamic actions (approve, edit, send) use HTMX to swap HTML fragments — no client-side JS state management needed.

---

## Hackathon Implementation Plan (36 Hours)

### Phase 1: Foundation [~40 min]
**Goal**: Server starts, renders a blank dashboard page

- [x] 1.1 Create project skeleton
  - [x] 1.1.1 Initialize git repo
  - [x] 1.1.2 Create all directories per project structure
  - [x] 1.1.3 Write requirements.txt
  - [x] 1.1.4 Create .gitignore (include .env, __pycache__, *.db, .venv/)
  - [x] 1.1.5 Create .env with GROQ_API_KEY placeholder
  - [x] 1.1.6 Set up Python virtual environment + install deps

- [x] 1.2 Core application setup
  - [x] 1.2.1 app/config.py — load env vars, define settings
  - [x] 1.2.2 app/database.py — SQLite engine, SessionLocal, Base, create_all on startup
  - [x] 1.2.3 app/models.py — all 6 SQLAlchemy ORM models
  - [x] 1.2.4 app/schemas.py — Pydantic schemas for API requests/responses
  - [x] 1.2.5 app/__init__.py

- [x] 1.3 FastAPI app + base template
  - [x] 1.3.1 app/main.py — FastAPI app, Jinja2 setup, lifespan (create tables + seed data), register routers
  - [x] 1.3.2 app/templates/base.html — layout with Pico CSS CDN, HTMX CDN, nav bar
  - [x] 1.3.3 app/templates/dashboard.html — empty state with "New Campaign" button
  - [x] 1.3.4 app/routers/pages.py — GET / renders dashboard
  - [x] 1.3.5 run.py — uvicorn entry point

- [x] 1.4 Verify: `python run.py` → browser shows dashboard at localhost:8000

---

### Phase 2: Synthetic Data [~30 min]
**Goal**: 500 realistic professional profiles loaded into DB on startup

- [x] 2.1 Profile generation script
  - [x] 2.1.1 scripts/generate_profiles.py — batch generate 500 profiles via Groq
  - [x] 2.1.2 20 batches of 25, each batch with diversity hints (industry, seniority mix)
  - [x] 2.1.3 Deduplicate by name
  - [x] 2.1.4 Write output to data/seed_profiles.json

- [x] 2.2 Seed loading
  - [x] 2.2.1 Startup hook in main.py: if profiles table empty, load from seed_profiles.json
  - [x] 2.2.2 Verify: restart server, check profiles are in DB

- [x] 2.3 Run the script, generate profiles, commit seed_profiles.json

---

### Phase 3: Goal Setup + Matching Engine [~1 hr]
**Goal**: User creates a goal, sees ranked contacts with match scores

- [x] 3.1 Groq client service
  - [x] 3.1.1 app/services/groq_client.py — chat(), chat_json(), retry with backoff

- [x] 3.2 Goal creation
  - [x] 3.2.1 app/templates/goal_setup.html — form with goal type dropdown, description textarea, background textarea, target roles, target companies
  - [x] 3.2.2 app/routers/goals.py — POST /api/goals to create goal
  - [x] 3.2.3 app/routers/pages.py — GET /goals/new renders form

- [x] 3.3 Matching engine
  - [x] 3.3.1 app/services/matching.py — prefilter_profiles() keyword/tag overlap scoring
  - [x] 3.3.2 app/services/matching.py — ai_rank_profiles() single Groq call for top ~50
  - [x] 3.3.3 Store rankings in DB (cache results per goal)

- [x] 3.4 Contacts page
  - [x] 3.4.1 app/templates/contacts.html — ranked list with score, match reason, checkboxes
  - [x] 3.4.2 app/templates/partials/contact_row.html — single contact row partial
  - [x] 3.4.3 app/routers/contacts.py — GET /api/goals/{id}/matches
  - [x] 3.4.4 app/routers/pages.py — GET /goals/{id}/contacts

- [x] 3.5 Verify: create goal → see ranked contacts with scores and reasons

---

### Phase 4: Template System + Message Generation [~1.5 hrs]
**Goal**: User picks a template, AI generates personalized drafts for selected contacts

- [x] 4.1 Template system
  - [x] 4.1.1 app/services/templates.py — seed 5 default templates on startup
    - Informational Interview
    - Internship/Job Inquiry
    - Research Collaboration
    - Investor Outreach
    - Custom
  - [x] 4.1.2 Each template has: intro, context, ask, closing sections with {variables}

- [x] 4.2 Template editor page
  - [x] 4.2.1 app/templates/template_editor.html — template type selector, tone dropdown, section previews, "Generate Messages" button
  - [x] 4.2.2 app/routers/pages.py — GET /goals/{id}/templates

- [x] 4.3 Message generation
  - [x] 4.3.1 app/services/outreach.py — generate_message() fills template per contact via Groq
  - [x] 4.3.2 app/services/outreach.py — batch_generate() for multiple contacts
  - [x] 4.3.3 app/routers/messages.py — POST /api/goals/{id}/generate

- [x] 4.4 Outreach page
  - [x] 4.4.1 app/templates/outreach.html — message draft cards with edit/approve buttons
  - [x] 4.4.2 app/templates/partials/message_card.html — single message card
  - [x] 4.4.3 app/routers/messages.py — PATCH /api/messages/{id} (edit), POST /api/messages/{id}/approve
  - [x] 4.4.4 app/routers/pages.py — GET /goals/{id}/outreach
  - [x] 4.4.5 HTMX inline editing for message body

- [x] 4.5 Verify: select contacts → pick template → see personalized drafts → edit and approve

---

### Phase 5: Sending Controls [~40 min]
**Goal**: Messages transition from approved → sent with rate limiting

- [ ] 5.1 Send config
  - [ ] 5.1.1 app/routers/messages.py — PUT /api/goals/{id}/send-config
  - [ ] 5.1.2 Send config UI on outreach page (max/day, warmup toggle, pause button)
  - [ ] 5.1.3 Default send_config created when goal is created

- [ ] 5.2 Send queue processor
  - [ ] 5.2.1 app/services/scheduler.py — process_queue()
    - Check send_config limits and pause state
    - Pick next N highest-priority approved messages
    - Mark as "sent", record sent_at
    - Respect max_per_day and warmup ramp
  - [ ] 5.2.2 app/routers/messages.py — POST /api/messages/{id}/send (single)
  - [ ] 5.2.3 app/routers/messages.py — POST /api/goals/{id}/send-batch (batch)

- [ ] 5.3 Manual vs automatic mode
  - [ ] 5.3.1 Manual: user approves each message, clicks send
  - [ ] 5.3.2 Automatic: approve-all + send-batch in one action

- [ ] 5.4 Verify: approve messages → send → status changes → respects daily limit

---

### Phase 6: Inbox Intelligence [~1 hr]
**Goal**: Sent messages get synthetic replies, classified by sentiment, with follow-up suggestions

- [x] 6.1 Synthetic reply generation
  - [x] 6.1.1 app/services/inbox.py — generate_synthetic_reply() via Groq
  - [x] 6.1.2 Trigger after send (~60-80% of messages get replies)
  - [x] 6.1.3 Randomized simulated timestamps (1-3 days after send)
  - [x] 6.1.4 For demo: generate immediately, display with future timestamp

- [x] 6.2 Reply classification
  - [x] 6.2.1 app/services/inbox.py — classify_reply() via Groq JSON mode
  - [x] 6.2.2 Returns sentiment (positive/neutral/negative) + key signal phrases

- [x] 6.3 Follow-up suggestions
  - [x] 6.3.1 app/services/inbox.py — suggest_follow_up() via Groq
  - [x] 6.3.2 Positive → schedule meeting / next steps
  - [x] 6.3.3 Neutral → provide more context / lighter ask
  - [x] 6.3.4 Negative → graceful close / alternative connection

- [ ] 6.4 Inbox page
  - [x] 6.4.1 app/templates/inbox.html — replies grouped by sentiment (color-coded)
  - [x] 6.4.2 app/templates/partials/reply_card.html — reply with sentiment badge, follow-up suggestion
  - [ ] 6.4.3 app/routers/inbox.py — GET /api/goals/{id}/inbox, POST /api/replies/{id}/follow-up
  - [ ] 6.4.4 app/routers/pages.py — GET /goals/{id}/inbox

- [ ] 6.5 Verify: sent messages → replies appear → correctly classified → follow-ups suggested

---

### Phase 7: Dashboard + Polish [~1 hr]
**Goal**: Polished dashboard with campaign stats and charts

- [ ] 7.1 Dashboard stats
  - [ ] 7.1.1 app/routers/goals.py — GET /api/goals/{id}/stats
  - [ ] 7.1.2 Metrics: messages sent, reply rate, sentiment breakdown, pending follow-ups
  - [ ] 7.1.3 app/templates/dashboard.html — stats cards, campaign list with status

- [ ] 7.2 Charts
  - [ ] 7.2.1 Chart.js via CDN — sentiment pie chart, messages over time bar chart
  - [ ] 7.2.2 Data injected via Jinja2 template variables

- [ ] 7.3 Visual polish
  - [ ] 7.3.1 Loading states (HTMX indicators)
  - [ ] 7.3.2 Success/error toast notifications
  - [ ] 7.3.3 Empty states with helpful CTAs
  - [ ] 7.3.4 Nav bar highlighting active page
  - [ ] 7.3.5 Responsive layout check

- [ ] 7.4 Demo readiness
  - [ ] 7.4.1 Seed DB with sample goal + messages + replies as fallback demo data
  - [ ] 7.4.2 Verify full end-to-end flow works smoothly
  - [ ] 7.4.3 Test with fresh DB (delete .db file, restart)

---

## End-to-End Pipeline Flow

```
1. User opens browser → GET / → Dashboard (empty state)
2. Clicks "New Campaign" → Goal Setup form
3. Enters goal ("ML internship"), background, preferences → POST /api/goals
4. System prefilters 500→50 profiles, Groq ranks top matches
5. Redirect → Contacts page with ranked list (score + reason per contact)
6. User selects contacts (checkboxes) → clicks "Next: Choose Template"
7. Template Editor → picks "Informational Interview", sets tone
8. Clicks "Generate Messages" → Groq generates personalized drafts
9. Outreach page → review drafts as cards, edit inline, approve
10. Set sending limits (max 10/day, warmup on)
11. Click "Send" → scheduler processes queue respecting limits
12. Synthetic replies generated for ~60% of sent messages
13. Inbox page → replies grouped by sentiment (green/yellow/red)
14. AI suggests follow-ups → user approves/sends
15. Dashboard shows stats: sent count, reply rate, sentiment chart
```

---

## Risk Mitigations

| Risk | Mitigation |
|------|-----------|
| Groq rate limits during demo | Pre-generate seed_profiles.json, cache rankings in DB |
| LLM returns malformed JSON | Groq JSON mode + try/except with retry |
| 500 profiles slow to rank | Prefilter to 50, single LLM call, cache results |
| Demo data missing | Seed DB with pre-built goal/messages/replies on startup |
| UI looks rough | Pico CSS handles typography/spacing; add minimal custom CSS |
| Something breaks live | Fallback: pre-seeded DB shows populated dashboard regardless |

---

## Commands

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Generate synthetic profiles (one-time)
python scripts/generate_profiles.py

# Run server
python run.py
# → http://localhost:8000

# Reset database
rm networking_ai.db && python run.py
```

---

## Conventions
- All LLM calls go through `services/groq_client.py` — never call Groq directly from routers
- HTMX partials return HTML fragments, not JSON — API endpoints used by HTMX return rendered templates
- JSON arrays stored as TEXT in SQLite — use `json.loads()`/`json.dumps()` in models
- Keep templates under 150 words — outreach messages should be concise
- Fixed message structure: intro → context → ask → closing — AI fills variables only, does not change structure
