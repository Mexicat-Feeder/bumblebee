# Bumblebee Standalone — Project Plan

**Goal:** A new user with a Windows laptop, an API key, and a PRD can go from zero to watching tickets get coded — using just a setup script and the dashboard.

**Status:** Draft — pending Pippin review

---

## Current State

What works today:
- **Engine** — full state machine, dispatch via OpenAI-compatible API, QA tiers 1-2, retry logic, guardrails
- **Dashboard** — SvelteKit + FastAPI, intake form, ticket views, gate progress, telemetry
- **new_project.py** — creates project scaffold, importable as library
- **decompose.py** — LLM decomposition with structured output, `generate_decomp_plan()` + `commit_plan()` ready to call
- **Config** — `api_base_url` + `api_key` in project-config.json, resolution chain (config → env → default)

What's Pixel-shaped (blocks standalone use):
- Intake flow sends a Telegram message to Pixel and waits for manual Q&A
- Decomposition requires Pixel to manually call decompose.py with a custom `llm_fn`
- Executor must be manually launched via `python run_executor.py` in a terminal
- Dashboard has no AI config UI — no way to set API URL, key, or model from the browser
- Install script sets up SSH for Pixel, not "install Bumblebee for a user"

---

## Architecture Decisions

### Two-model setup

| Phase | Default model | Why |
|---|---|---|
| Q&A (PRD refinement) | Local — Lemonade (Qwen 3.6 27B) | Free, always available, good enough for clarifying questions |
| Decomposition (PRD → tickets) | Local — Lemonade | Structured output, single-call |
| Coding (Forge dispatch) | User's configured API | Multi-file coordination needs the best model available |

All three are independently configurable in the dashboard. Users can run everything local, everything cloud, or mix.

### Q&A replaces Pixel with a local LLM

Current flow: User uploads PRD → Pixel reads it → Pixel asks clarifying questions via Telegram → user answers → Pixel writes VISUAL-SPEC.md + ARCHITECTURE-SUMMARY.md → Pixel decomposes.

New flow: User uploads PRD → dashboard opens a chat window → local LLM (reading the PRD as context) asks clarifying questions → user answers in the chat → LLM produces a decision summary → summary feeds into decomposition alongside the PRD.

The chat system prompt uses the Q&A checklist from DECOMPOSITION-PROCESS.md (runtime/infra, tech stack, design/UX, scope/priorities). The LLM doesn't need to be as good as Claude — it just needs to surface questions the PRD doesn't answer.

### Lemonade auto-detection

Dashboard probes `http://[::1]:13305/v1/models` on startup. If Lemonade is running:
- Show available models in a dropdown for Q&A and decomposition
- Pre-select the best available model
- Show "Local AI: connected" indicator

If Lemonade is not running:
- Q&A and decomposition fields show "Configure API endpoint" instead
- User can manually enter any OpenAI-compatible endpoint

### Per-phase model configuration

The dashboard settings panel lets the user configure three model slots:

```
┌─────────────────────────────────────────────┐
│ AI CONFIGURATION                            │
│                                             │
│ Q&A Model (PRD refinement)                  │
│ ┌─────────────────────────────────────────┐ │
│ │ ▼ Lemonade: Qwen3.6-27B-GGUF          │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ Decomposition Model (ticket planning)       │
│ ┌─────────────────────────────────────────┐ │
│ │ ▼ Lemonade: Qwen3.6-27B-GGUF          │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ Coding Model (Forge)                        │
│ ┌─────────────────────────────────────────┐ │
│ │ ▼ Custom API                           │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ Custom API Settings                         │
│ Base URL: [https://api.openai.com/v1      ] │
│ API Key:  [sk-•••••••••••••••             ] │
│ Model:    [gpt-4o                         ] │
│                                             │
│ Each dropdown shows:                        │
│ - Lemonade models (auto-detected)           │
│ - "Custom API" (uses fields below)          │
└─────────────────────────────────────────────┘
```

This flows into `project-config.json` as:

```json
{
  "models": {
    "qa": "Qwen3.6-27B-GGUF",
    "decomp": "Qwen3.6-27B-GGUF",
    "forge": "gpt-4o",
    "vision": "gpt-4o"
  },
  "api_base_url": "https://api.openai.com/v1",
  "api_key": "sk-...",
  "lemonade_url": "http://[::1]:13305"
}
```

Engine's `direct_dispatch.py` already reads `api_base_url` and model from config — this just makes it configurable from UI.

---

## Phases

### Phase 0: AI Config UI + Lemonade Detection

**What:** Add AI configuration to the dashboard intake form.

**Deliverables:**
- New `AIConfigSection.svelte` component — model dropdowns, API fields, Lemonade auto-detect
- New API route `GET /api/lemonade/models` — probes Lemonade, returns available models
- New API route `GET /api/ai/config` + `PATCH /api/ai/config` — global AI defaults (persisted in dashboard config)
- Update `SettingsSection.svelte` — embed AI config or show alongside
- Update project creation flow — AI config values flow into `project-config.json`
- Store global AI defaults in `dashboard.config.json` so new projects inherit them

**Verification:** Open dashboard → see Lemonade models in dropdown (if running) → create project → check project-config.json has correct API settings.

### Phase 1: Q&A Chat Widget

**What:** Embedded chat window in the intake flow. Local LLM reads the PRD and asks clarifying questions.

**Deliverables:**
- New `QAChat.svelte` component — chat UI (messages list, input, send button)
- New API route `POST /api/projects/{slug}/qa/chat` — proxies to configured Q&A model with conversation history + PRD context
- System prompt based on DECOMPOSITION-PROCESS.md Q&A checklist
- "Finish Q&A" button — LLM produces a decision summary from the transcript
- Summary saved as `qa-summary.md` in project directory
- Chat transcript saved for decomposition context

**Verification:** Upload PRD → chat with LLM → LLM asks relevant questions → click Finish → summary appears → status advances to `qa_complete`.

**Key design:** The chat is stateful server-side (conversation stored in registry or JSON file per project). Refreshing the page resumes the conversation. The LLM doesn't stream responses (simpler) — it returns complete messages.

### Phase 2: Self-Service Decomposition

**What:** Dashboard calls decompose.py directly. No Pixel involvement.

**Deliverables:**
- New API route `POST /api/projects/{slug}/decompose` — calls `generate_decomp_plan()` with real `llm_fn`
- `llm_fn` implementation that calls the configured decomp model via OpenAI-compatible API
- Feeds PRD text + Q&A summary as context
- New `DecompReview.svelte` component — shows generated tickets grouped by gate, allows approve/reject
- "Approve Plan" commits to DB via `commit_plan()`
- "Re-decompose" button to retry with different context
- Remove Telegram notification from `begin-qa` flow (or make it optional)

**Verification:** After Q&A → click Decompose → see ticket plan → approve → tickets appear in DB → dashboard ticket views show them.

### Phase 3: Executor Management

**What:** Dashboard can start/stop the coding engine per project.

**Deliverables:**
- New API route `POST /api/projects/{slug}/executor/start` — spawns `run_executor.py` as subprocess
- New API route `POST /api/projects/{slug}/executor/stop` — kills the subprocess
- New API route `GET /api/projects/{slug}/executor/status` — running/stopped/error + last cycle info
- PID file per project for reattach after dashboard restart
- New `ExecutorControl.svelte` component — start/stop button, status indicator, last error
- Executor stdout/stderr captured to log file, tailable from dashboard
- New API route `GET /api/projects/{slug}/executor/logs` — returns recent log lines

**Verification:** Approve tickets → click Start → executor processes tickets → dashboard shows progress → click Stop → executor halts cleanly.

### Phase 4: Install Script + Service

**What:** One-command install for new users. Dashboard runs as a service.

**Deliverables:**
- `install.ps1` — PowerShell script that:
  - Checks/installs Python 3.11+ (winget)
  - Checks/installs Node.js 18+ (winget)
  - Clones repo (or works with existing clone)
  - Installs Python deps (`pip install -r`)
  - Builds dashboard frontend (`npm install && npm run build`)
  - Creates `dashboard.config.json` from example
  - Registers dashboard as Windows Scheduled Task (starts at logon, restarts on crash)
  - Opens browser to `http://localhost:8765`
- `uninstall.ps1` — removes scheduled task, optionally removes repo
- First-run detection in dashboard — if no projects exist, redirect to intake form with setup wizard

**Verification:** Fresh Windows machine → run install script → dashboard opens → create first project → full flow works.

### Phase 5: Documentation

**What:** README rewrite for standalone users.

**Deliverables:**
- New README.md focused on user journey (not internals)
- Sections: What is Bumblebee, Requirements, Install, Your First Project, How It Works, Troubleshooting
- Remove all Pixel/OpenClaw/swarm assumptions
- Add screenshots of dashboard flow
- Keep technical architecture docs as separate files for contributors
- DECOMPOSITION-PROCESS.md stays but gets a note that Q&A is now automated

---

## Implementation Strategy

This is dashboard + API work. The engine itself barely changes — it already supports everything through config.

**Who does the work:** Bumblebee/Forge for isolated components (chat widget, AI config panel, decomp review). Pixel for API routes and integration wiring (Rule 6). Install script is scripting, not app code — Pixel writes directly.

**Order matters:** Phase 0 (AI config) unblocks everything else. Phase 1-2 (Q&A + decomp) are the core value. Phase 3 (executor mgmt) is quality-of-life. Phase 4-5 (install + docs) are the packaging.

**What doesn't change:**
- Engine state machine, dispatch, QA — untouched
- Existing dashboard views (tickets, gate progress, telemetry) — untouched
- SPEC-RULES.md, DECOMPOSITION-PROCESS.md — content preserved, delivery mechanism changes

---

## Open Questions

1. **Streaming chat responses?** Simpler to do request/response. Streaming is nicer UX but adds SSE complexity to the chat route. Recommendation: start without streaming, add later if users want it.

2. **Global vs per-project AI config?** Proposal: global defaults in dashboard config, per-project overrides in project-config.json. New projects inherit global defaults. User can change per-project in the intake form.

3. **Lemonade model management?** Should the dashboard show loaded vs available models? Let users load/unload? Or just show what's currently loaded and let Lemonade manage itself? Recommendation: show loaded models only, don't manage Lemonade lifecycle.

4. **What about non-Windows?** The install script is PowerShell/Windows. Linux/Mac users can follow manual steps in README. Add cross-platform install later if there's demand.
