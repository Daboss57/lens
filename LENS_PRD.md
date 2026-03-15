# LENS — Product Requirements Document
**Self-Hosted LLM Observability**
*PRD v1.0 · March 2026 · Built by Noel*

> A zero-dependency, open-source observability stack for LLM-powered applications. One command to deploy. Every prompt, response, token count, latency, cost, and failure — captured locally, visualized in real-time, analyzed by AI.

**Tags:** `Open Source` `Self-Hosted` `Multi-Provider` `AI-Powered Analysis`

---

## 01 — Executive Summary

| Field | Value |
|---|---|
| **Product** | LENS |
| **Tagline** | Ship AI apps. See everything. Pay nothing. |
| **Category** | Developer Tools / LLM Infrastructure / Observability |
| **Stage** | Open Source MVP → GitHub Launch |
| **Builder** | Noel (indie) |

### The Problem
Every developer building on LLM APIs — OpenAI, Anthropic, Gemini, Mistral — is flying blind. They don't know which prompts are failing, which calls are burning cost, or why their agent loops sometimes go infinite. The tools that exist (Langfuse, Helicone, Braintrust) solve this, but they're cloud-first, require accounts, and eventually charge per event. For indie builders and small teams, that's friction and eventual cost at the worst time.

### The Solution
LENS is a single Docker container you spin up in 60 seconds. Drop one SDK wrapper around your existing LLM calls. Every request is captured, stored in local SQLite, and surfaced in a real-time web dashboard — latency timelines, cost breakdowns, session replay, failure heatmaps. An AI analysis layer (powered by Claude) runs in the background and tells you what's actually going wrong: which prompts degrade over long sessions, where token waste is highest, and what to fix first. Fully offline. Zero data leaves your machine.

### Why Now
LLM API usage among indie developers has exploded since late 2024. The tooling ecosystem around observability is consolidating toward SaaS pricing models, leaving a clear gap for a self-hosted open-source alternative. Docker adoption is near-universal among developers. The combination of cheap local SQLite, React dashboards, and LLM-powered analysis was not practical at this quality level two years ago.

---

## 02 — Problem Statement

When a developer ships an LLM-powered feature — a chatbot, an agent, a code assistant — they enter a black box. API calls go out. Responses come back. Sometimes they're wrong, slow, or expensive. The developer has no idea which calls are problematic, how costs are distributed across sessions, or whether their system prompt is degrading after turn 8 in a conversation. This isn't a niche problem — it's the default state of every LLM app in production.

### Pain Signals from the Community
- "I have no idea what my OpenAI bill is until it hits at the end of the month" — r/LocalLLaMA
- "Is there anything like Datadog but for prompt chains? I'm debugging blind" — r/MachineLearning
- "Langfuse is great but I don't want another SaaS subscription for a side project" — HackerNews
- "My agent randomly goes into infinite loops and I have zero visibility into why" — r/LangChain
- "I need to see the actual token-by-token cost per user session before I can price this thing" — indie builder, X

### Why Existing Solutions Fall Short

| Tool | Problem |
|---|---|
| **Langfuse** | Cloud-first, account required, pricing scales with events, privacy concerns for sensitive prompts |
| **Helicone** | SaaS proxy model — routes traffic through their servers. Not self-hostable in free tier. |
| **Braintrust** | Powerful but expensive and enterprise-oriented. Overkill for indie builders and small teams. |
| **LangSmith** | LangChain-specific, limited multi-provider support, cloud dependency |
| **Roll your own logs** | Most devs just use print() or basic logging — zero structure, no visualization, no analysis |

---

## 03 — Solution Overview

LENS intercepts LLM API calls via a lightweight Python SDK wrapper (drop-in replacement for the standard clients) and a local ingestion server. All trace data — request payload, response, latency, token counts, cost, session ID, model, provider — is written to a local SQLite database. A FastAPI backend serves this data to a React dashboard with real-time WebSocket updates. An AI analysis layer runs periodic or on-demand jobs using Claude to surface actionable insights: failure patterns, cost hotspots, prompt degradation trends.

### Core Value Proposition
> The only LLM observability tool that is fully local, zero-config, provider-agnostic, and ships with AI-powered failure analysis — runnable in one command, forever free.

### What LENS is NOT
- Not a cloud product — no accounts, no servers, no data leaving your machine
- Not an LLM testing / evals framework (that's Braintrust territory)
- Not a prompt management tool (no versioning, A/B testing, or prompt libraries)
- Not a deployment platform or LLM gateway / proxy
- Not production monitoring at enterprise scale (this is for builders, not ops teams)

---

## 04 — Target Users

### Primary ICP
Indie developers and small teams (1–5 people) building LLM-powered applications: chatbots, agents, AI features embedded in SaaS products. They're actively making API calls to OpenAI, Anthropic, or Gemini. They care about cost and reliability but don't have budget for observability tooling. They're comfortable running Docker locally or on a cheap VPS. They find out about tools through Reddit (r/LocalLLaMA, r/SideProject), HackerNews, and X.

### User Personas

**Alex, 24 — Indie Hacker**
Building a B2B SaaS with an AI writing assistant. Paying ~$200/mo in OpenAI API costs. Has no idea which features or users are driving that spend. Wants a cost breakdown by session and user before he prices the product. Comfortable with Docker. Won't pay for another SaaS subscription.

**Priya, 28 — Solo ML Engineer**
Working on a multi-agent research tool using LangChain and Claude. Her agent loops occasionally go infinite and she can't reproduce the issue. Needs session replay to see exact call sequences. Has tried LangSmith but hates the LangChain lock-in.

**James, 19 — CS Student / Builder**
Side-projecting a code review bot and a Kalshi trading agent. No budget. Runs everything locally. Wants visibility into what his agents are actually doing without paying for observability tools. Will star a good GitHub repo and tell his Discord about it.

---

## 05 — Key Features (MVP Scope)

### Core — Must Have

| Feature | Description | Complexity |
|---|---|---|
| **SDK Wrapper** | Drop-in replacement for openai, anthropic, google.generativeai clients. Zero code change required beyond the import. | Low |
| **Ingestion Server** | FastAPI endpoint that receives trace events from SDK wrapper, validates, and writes to SQLite. | Low |
| **Real-Time Dashboard** | React web UI showing live feed of LLM calls with latency, tokens, cost, model, status. | Med |
| **Session Replay** | Click any session and replay the full conversation turn-by-turn with metadata at each step. | Med |
| **Cost Tracker** | Per-call and cumulative cost calculation using provider pricing tables. Daily/weekly cost charts. | Low |
| **Failure Detection** | Automatic tagging of failed calls (errors, timeouts, empty responses, rate limits) with summary counts. | Low |
| **Docker Compose Deploy** | Single `docker-compose up` that starts ingestion server + dashboard. No setup beyond Docker. | Low |
| **Multi-Provider Support** | Works with OpenAI, Anthropic, Gemini, Mistral, Groq, OpenRouter out of the box. | Med |

### Enhanced — Nice to Have (Post-MVP)
- AI Failure Analysis — Claude-powered background job that surfaces failure patterns, suggests prompt fixes
- Prompt Degradation Alerts — detect when response quality drops across a long multi-turn session
- User/Session Attribution — tag calls with user IDs to see per-user cost and behavior
- Export to CSV/JSON — export any date range of traces for offline analysis
- Slack / Discord webhook alerts — notify when cost spikes or error rate exceeds threshold
- LLM Latency Benchmarking — compare provider latency side-by-side on the same prompts

### Out of Scope (v1)
- Prompt versioning or A/B testing
- Cloud hosting or multi-machine sync
- Fine-tuning pipeline integration
- Custom model / self-hosted LLM support (Ollama etc.) — stretch goal only

---

## 06 — User Flows

### Onboarding Flow
1. Developer finds LENS on GitHub or Reddit
2. Runs: `git clone && docker-compose up -d`
3. Installs the LENS Python SDK: `pip install lens-sdk`
4. Replaces `import openai` with `import lens.openai as openai` (one line change)
5. Runs their existing application — all LLM calls are now captured automatically
6. Opens `localhost:4200` — dashboard is live with real data from the first call
7. No account creation, no API key for LENS, no configuration required

### Core Use Case Flow — Debugging a Failing Agent
1. Developer notices their agent is returning empty responses intermittently
2. Opens LENS dashboard → clicks 'Failures' filter in the live feed
3. Sees 3 failed calls in the last hour — all on the same session ID
4. Clicks session ID → enters Session Replay view
5. Replays the conversation turn-by-turn — sees that on turn 9, context window exceeded
6. Identifies the exact prompt turn that caused the overflow
7. Fixes the issue in their code — confirms in LENS that failures drop to zero

### Cost Analysis Flow
1. Developer wants to understand API spend before setting pricing for their product
2. Opens LENS → Cost tab → selects last 7 days
3. Sees breakdown by model, by feature (tagged via session metadata), by day
4. Identifies that the 'summarize document' feature costs 4x more than the chat feature
5. Exports the data as CSV to share with co-founder
6. Adjusts feature pricing accordingly

---

## 07 — Technical Architecture

### Stack Overview

| Layer | Technology | Rationale |
|---|---|---|
| **SDK Wrapper** | Python — monkey-patches provider clients | Zero friction adoption, works with existing code |
| **Ingestion API** | FastAPI + Uvicorn | Fast async HTTP, Noel's default backend, easy to extend |
| **Storage** | SQLite + SQLAlchemy ORM | Zero-dependency DB, perfect for local-first, sufficient for indie scale |
| **Real-Time** | WebSockets (FastAPI native) | Live dashboard updates without polling overhead |
| **Frontend** | React + TypeScript + Vite | Fast dev iteration, Recharts for visualization, Tailwind for styling |
| **Deployment** | Docker + Docker Compose | Single command setup, no external dependencies |
| **AI Analysis** | Anthropic Claude API (optional) | Background analysis jobs — user supplies their own key |

### Core Data Model
Three primary entities:
- **Trace** — one per LLM API call. Stores request, response, metadata, timing, cost.
- **Session** — groups Traces by conversation or agent run, identified by `session_id` tag.
- **Analysis** — AI-generated insights attached to a Session or time window. Generated asynchronously.

Traces are append-only. Sessions are derived. Analysis records are generated asynchronously.

### Trace Schema
```json
{
  "trace_id": "uuid",
  "session_id": "my-chatbot-user-123",
  "provider": "openai",
  "model": "gpt-4o",
  "request": { "...full payload..." },
  "response": { "...full response..." },
  "prompt_tokens": 842,
  "completion_tokens": 156,
  "cost_usd": 0.00312,
  "latency_ms": 1240,
  "status": "success",
  "error_msg": null,
  "timestamp": "2026-03-14T02:33:00Z"
}
```

### Key Design Decisions
- **SDK as monkey-patch** — wraps provider clients at import time, users change one line not their entire codebase
- **Local SQLite over Postgres** — removes need for any external database service in default setup
- **Optional Claude integration** — AI analysis requires user's own key, core product works without it
- **WebSocket for live feed** — dashboard feels alive without polling, backend pushes new traces as they arrive
- **Single Docker Compose** — entire stack (API + frontend + DB) comes up with one command

---

## 08 — Competitive Landscape

| | LENS | Langfuse | Helicone | Braintrust | LangSmith |
|---|---|---|---|---|---|
| Self-hosted | ✓ | ✓ (complex) | ✗ | ✗ | ✗ |
| Zero-config | ✓ | ✗ | ✗ | ✗ | ✗ |
| Multi-provider | ✓ | ✓ | ✓ | ✓ | ✗ |
| AI analysis | ✓ | ✗ | ✗ | Partial | ✗ |
| Free forever | ✓ | Partial | Partial | ✗ | Partial |
| Session replay | ✓ | ✓ | ✗ | ✓ | ✓ |
| One-line SDK | ✓ | ✗ | Partial | ✗ | ✗ |

**Honest Assessment:** Langfuse is the closest competitor and has self-hosted support. But its setup complexity (Postgres, Redis, multiple services) is a meaningful barrier for solo builders. LENS wins on simplicity and the AI analysis layer. If Langfuse adds a simple local mode, LENS's window narrows — but community momentum and the one-line SDK remain strong differentiators.

---

## 09 — Go-to-Market Strategy

### Launch Channels
- **r/LocalLLaMA** — Largest engaged community of LLM builders. Post: *"I was blind to what my LLM app was doing, so I built a self-hosted observability tool"*
- **r/SideProject + r/selfhosted** — Both communities love open-source, self-hosted tools with clean demos
- **HackerNews Show HN** — High-signal audience, strong potential for star spike if the demo is clean
- **X / Twitter** — Short demo video: 60 seconds from zero to live dashboard. Tag @karpathy, @swyx, @_joshma
- **Dev.to / Hashnode** — *"I built Langfuse but local — here's how it works"* — SEO + community traction

### The Demo That Gets Shared
The single most important asset for launch is a 60-second screen recording showing: (1) a Python script making real OpenAI/Claude calls, (2) one-line SDK change, (3) `docker-compose up`, (4) the dashboard lighting up live with calls as they happen, showing cost, latency, session replay. No slides, no voiceover fluff — just the product working.

### Pricing
Fully free and open source (MIT license). LENS itself has no pricing — the AI analysis feature requires the user to supply their own Anthropic API key, keeping LENS's infrastructure costs at zero.

> **Visa note:** Noel is on H4 and cannot legally collect income in the US at this time. LENS is positioned as an open-source portfolio project. Revenue collection would require F1 → OPT status change or routing through a parent entity.

---

## 10 — Metrics & Success Criteria

**North Star Metric:** GitHub Stars

| Metric | 30 Days | 90 Days | 180 Days |
|---|---|---|---|
| GitHub Stars | 500+ | 2,000+ | 5,000+ |
| Contributors (PRs merged) | 3+ | 15+ | 40+ |
| Reddit post upvotes (launch) | 200+ | — | — |
| Forks | 50+ | 300+ | 800+ |
| Issues opened | 20+ | 100+ | 250+ |

---

## 11 — Risks & Open Questions

### Technical Risks
- SDK monkey-patching can break on provider client updates — need to pin versions and test on each release
- SQLite may become a bottleneck at high call volumes — acceptable for MVP but needs flagging
- WebSocket real-time at high frequency (>100 calls/sec) may overwhelm the dashboard — needs throttling
- Claude API dependency for AI analysis means cost exposure if analysis runs too frequently

### Market Risks
- Langfuse ships a simplified self-hosted mode — their existing brand eats LENS's primary differentiator
- Developer attention is fragmented — good tools still fail to get traction without sustained distribution push
- The "one-line SDK" pitch only works if providers don't dramatically change their client interfaces

### Legal / Visa
- ✅ H4 visa: LENS is open-source, no income collection — fully permissible
- ✅ MIT license is clean for commercial use by others — does not implicate builder income
- ⚠️ Users should be warned: full prompt/response payloads are stored locally. They are responsible for their own privacy compliance (GDPR, HIPAA, etc.)
- ⚠️ AI analysis layer sends traces to Anthropic API — must be opt-in with explicit warning in UI

### Open Questions Before Building
- What's the cleanest monkey-patch strategy for all 4+ providers without breaking type hints?
- Should the dashboard be a standalone React app or server-side rendered via FastAPI Jinja2?
- What's the right schema for session attribution — how should users tag their calls?
- Does the AI analysis layer need its own queue/worker, or can it run as a FastAPI background task?

---

## 12 — Roadmap

### Phase 1 — MVP (Weeks 1–2)
- [ ] SDK wrapper for OpenAI + Anthropic
- [ ] FastAPI ingestion server with SQLite storage
- [ ] Basic React dashboard: live feed, cost totals, failure count
- [ ] Docker Compose single-command deploy
- [ ] README with install instructions, demo GIF, one-line setup
- [ ] GitHub repo launch — first Reddit/X post

### Phase 2 — Polish & Depth (Weeks 3–4)
- [ ] Session Replay UI — click any session, see full conversation tree
- [ ] Cost breakdown charts (by model, by day, by session)
- [ ] Failure detection and tagging with error classification
- [ ] Add Gemini, Mistral, Groq, OpenRouter SDK wrappers
- [ ] Export to CSV/JSON
- [ ] HackerNews Show HN launch

### Phase 3 — AI Layer & Community (Month 2+)
- [ ] Claude-powered AI analysis: failure pattern summaries, prompt fix suggestions
- [ ] Prompt degradation detection across multi-turn sessions
- [ ] Slack/Discord webhook alerts for cost spikes and error rate thresholds
- [ ] Contributor onboarding — CONTRIBUTING.md, good-first-issue tags
- [ ] Hosted cloud version exploration (if community demand warrants it)

---

*LENS — PRD v1.0 · March 2026 · Built by Noel*
