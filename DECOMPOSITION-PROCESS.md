# PRD → Working App: Decomposition Process

**Status:** Final — approved by Root
**Last updated:** 2026-05-06

---

## Problem Statement

Twice now, Pixel decomposed Remy's PRD into tickets and ran Forge. Both times:
- All files were written
- Build passed
- App crashed on first real interaction

**Root cause:** Tickets were scoped as "write this file" instead of "make this feature work." File existence is not functionality. Local models are great at generating syntax but terrible at maintaining unprompted global context.

---

## What Went Wrong

### Attempt 1 (batch run, May 5)
- 13 tickets, all UI shell + stub routes
- Backend routes returned placeholder data with TODO comments
- "Functional backend stubs" = not functional at all

### Attempt 2 (Pixel decomposition, May 6)
- 22 tickets, real API integration code
- Files had real fetch() calls to Lemonade, real WebSocket to ComfyUI
- But: no error handling, no prerequisite checks, no startup sequence
- Talk button → unhandled error → UI crash
- Type anything → API fails → component unmounts → blank screen
- Voice models not loaded in Lemonade, ComfyUI not running
- QA was "file exists and > 150 bytes" — not "feature works"

### The pattern
Both attempts followed: PRD → file list → write files → check files exist → "done"

This produces **code artifacts**, not **working software**.

---

## Lessons

1. **A file is not a feature.** `lemonadeService.ts` existing doesn't mean voice works.
2. **Integration is where things break.** Individual files can be syntactically perfect and the app still crashes on first use.
3. **Error handling is not optional.** An app that crashes when a dependency is unavailable is not a working app — it's a demo that only works under perfect conditions.
4. **Local models will not add error handling unprompted.** They optimize for the happy path. Error boundaries, fallbacks, and graceful degradation must be explicitly mandated in every ticket.
5. **QA must test behavior, not existence.** "File > 150 bytes" catches empty stubs but not broken code.
6. **Prerequisites matter.** If the app needs Lemonade with specific models and ComfyUI running, something must ensure that before the app tries to use them.
7. **The local model can write correct-looking code.** Qwen3.6 produced syntactically valid TypeScript with real API calls. The problem isn't code quality — it's that nobody tested whether the code actually works end-to-end.

---

## The Process

### Q&A Checklist

Before writing architecture or specs, Pixel conducts a Q&A with the human to surface decisions the PRD doesn't cover. The PRD is the "what" — Q&A fills in the "how" and "with what." Do not assume answers. If the PRD doesn't specify, ask.

**Runtime & Infrastructure**
- Which Lemonade model should this project target? (name, size, reasoning vs non-reasoning)
- What port should the app run on? Any port conflicts with existing services?
- Where should the deliverable files live? (`Documents/<slug>` default, or somewhere else?)
- Any external services beyond what the PRD lists? (databases, APIs, hardware)
- Auth or access restrictions? (localhost only, network-accessible, password-protected)

**Tech Stack**
- Does the human have a preference on framework/language, or should Pixel decide?
- Any existing code or libraries to integrate with?
- Any packages/dependencies the human has already installed or wants to avoid?
- Build system preference? (none for simple projects, Vite/webpack for complex ones)

**Design & UX**
- Visual reference priority: exact match, inspired by, or just general direction?
- Target browsers or devices? (desktop only, mobile, specific browser)
- Any accessibility requirements?
- Expected number of users? (affects whether a production server matters)

**LLM-Specific** (when the project calls an LLM)
- Which model exactly? (model ID as listed in `Invoke-RestMethod -Uri "http://[::1]:13305/v1/models"`)
- Reasoning model or non-reasoning? (affects max_tokens budget — reasoning models burn tokens on thinking)
- What temperature / max_tokens? Or leave to Pixel's judgment?
- Hardcode the model name or make it configurable?

**Scope & Priorities**
- What's the simplest version that counts as done?
- Any features mentioned in the PRD that should be deferred to v2?
- How should errors be presented? (technical detail vs friendly message)

Not every question applies to every project. Skip what's obvious, ask what isn't. The output of Q&A is the VISUAL-SPEC.md and ARCHITECTURE-SUMMARY.md — these capture the decisions.

### Phase 0: Prerequisites & Environment

Before any app code gets written, produce:

1. **Dependency manifest** — what external services, models, ports, directories does this app need?
2. **Health-check script** — verifies all prerequisites are met. Returns structured pass/fail per dependency. Config-driven — reads from a generic `healthChecks` array in the project config, not hardcoded service names. See [Health Check Config](#health-check-config).
3. **Mock services** — lightweight stubs for every external dependency, returning canned responses. Used for QA tiers 1–4 so builds and tests don't require live backends. See [Mock Services](#mock-services) section.
4. **Boot guard** — the app checks prerequisites on startup. If a required service is down, show a status page (web apps) or log structured status (headless workers), not a crash. Fail fast with clear status output to prevent cascading errors. Implementation is framework-specific but the pattern is universal: read service list from project config → check on startup → poll periodically → never crash on missing dependencies.

**This phase produces runnable artifacts** — the health check and mocks are tested before any feature tickets are written.

#### Build-system language policy

App code uses whatever stack fits the project (TypeScript, Python, etc.). Build-system tooling — health checks, mock engine, start/stop scripts — standardizes on TypeScript + Node.js. Node.js is a dev dependency for all projects, not a runtime dependency. This avoids maintaining parallel tooling in multiple languages while keeping each project's app code in its natural stack.

### Phase 1: Skeleton That Runs

First milestone is not "all files exist" — it's **"the app starts and doesn't crash."**

- App starts, serves its primary interface, responds to a health endpoint
- UI renders without errors (web apps) or worker reaches expected state (headless)
- API routes / handlers return structured error responses when backends aren't available
- App-level connection state context is established (see [State Management](#state-management))
- Status indicators appear when dependencies are down — individual features show "offline" state

#### Gate variants by project type

**Web apps (Remy, Dashboard, any project with a browser UI):**
Start app → open browser → see UI → no console errors → `/api/health` returns 200 with dependency status → stop a mock service → banner appears, no crash.

**Headless workers (Conference Analytics vision worker, any non-web component):**
Start worker with mocks → verify it reaches expected running state (via structured log output or health file) → health output includes dependency status → kill a mock dependency → worker transitions to degraded/reconnecting state within timeout → no crash, no hung process.

**Hybrid projects (Conference Analytics = vision worker + dashboard):**
Both gates apply. The worker gate and the web gate are tested independently. A project can have multiple Phase 1 gates if it has multiple runnable components.

### Phase 2: Vertical Slices

Don't build "all frontend" then "all backend." Build one feature end-to-end at a time.

Each slice:
- Has a concrete acceptance test (steps a human or script can follow)
- Includes error handling for that slice's failure modes
- Is independently verifiable
- Includes both frontend and backend code for the feature

**Run smoke tests after each vertical slice, not batched at the end.** If Slice 2 introduces a state bug, you don't want Forge hallucinating workarounds in Slice 3 to compensate for a broken foundation. Stop the line, fix the slice, then proceed.

### Phase 3: Error Boundaries & Resilience

After features work under ideal conditions, explicitly test failure modes:
- What happens when each dependency is down?
- What happens when an API returns unexpected data?
- What happens when hardware isn't available (mic, webcam, GPU)?
- **Each failure mode gets a graceful UI state**, not a crash

### Phase 4: Polish & Integration

Two stages:

**Stage A: Pixel vision review (up to 3 rounds, no human input)**

Pixel screenshots the running app, compares against visual references + VISUAL-SPEC + project goals, and writes Forge tickets for visual/layout issues. Feedback is driven by the project's audience and purpose, not mechanical pixel-matching against reference images. References inform style; common sense informs hierarchy, sizing, and readability.

Each round: screenshot → compare → tickets → Forge → screenshot. Hard limit: 3 rounds. If not converging after 3, stop and move to Stage B.

Typical issues caught: component sizing vs visual importance, typography scale for readability at distance, color/accent consistency with design tokens, panel proportions, visual hierarchy (what draws the eye first).

**Stage B: Human review gate (required for close)**

Human reviews the current state and provides feedback. UI and UX work requires explicit human sign-off before Phase 4 closes. The human may drive additional ticket rounds, but the goal is that Stage A gets 80-90% of the way there.

**Also in Phase 4:**
- Cross-feature interactions
- Performance tuning
- Startup sequence / installer

---

## Ticket Structure

Every ticket must include these fields:

### Required fields
- **Objective:** What user-visible behavior does this ticket produce?
- **Acceptance test:** Concrete steps a human (or script) can follow to verify it works. Must be verifiable with mock services running.
- **Files to write:** The implementation artifacts
- **Context files:** Existing code the model MUST read to integrate correctly. **Max 3 context files per ticket.** Local models hallucinate integrations if they can't see adjacent code, but too many reads exhausts context.
- **Dependencies:** What tickets/features must be working before this one
- **Error handling:** Explicit requirements for what happens when things go wrong. Not optional — Forge will not add error handling unless the ticket mandates it.
- **Smoke test:** A curl/fetch command or script that verifies the feature works. Must include a **runtime** check (start server + curl endpoint), not just a build check. Populates `qa_cmd_json`.
- **API patterns:** Exact usage patterns for any library APIs the ticket requires. See [Writing Specs for Forge](#writing-specs-for-forge).

### Example: Text Chat Ticket (Remy)

**Objective:** User can type a message to Remy and get a conversational response with an updated prompt.

**Acceptance test:**
1. Start the app (frontend + backend + mock Lemonade)
2. Open http://127.0.0.1:4177
3. Type "make a pixel art cat" in the chat input
4. Click Send
5. Verify: chat shows user message AND assistant reply
6. Verify: prompt field updates with a generation prompt
7. Stop mock Lemonade → verify chat shows "Remy is offline" instead of crashing

**Files:** src/server/routes/voice.ts, src/server/services/lemonadeService.ts, (updates to) src/components/RemyPanel.tsx

**Context files:** src/shared/api-types.ts, src/App.tsx (to see how state flows)

**Error handling:** If Lemonade returns non-200, catch and return `{ error: "Remy is offline — check that Lemonade is running" }`. Frontend shows error in chat log, does not crash. Generate button stays disabled.

**Smoke test:** `curl -X POST http://127.0.0.1:4178/api/remy/chat -H "Content-Type: application/json" -d '{"message":"hello","mode":"txt2img","history":[]}' | jq .reply`

---

## Writing Specs for Forge

Forge (Qwen3.6-35B) is a capable coder but not a mind reader. Specs must be precise enough that Forge doesn't need to guess. These rules come from empirical testing (see `bumblebee/FORGE-TEST-RESULTS.md`).

### Forge capabilities (tested 2026-05-06)
- ✅ Write 1-8 new files per ticket from clear specs
- ✅ Read 2-3 context files and use them correctly (imports, types, patterns)
- ✅ Modify existing files with targeted changes (read file, add specific code, keep everything else)
- ✅ Chain tickets — read previous ticket's output and import correctly
- ✅ Complex integration code (WebSocket, SSE, job tracking, React context)
- ✅ Self-correct build errors when told "run build, fix errors"
- ❌ Guess library APIs it hasn't seen (gets details wrong)
- ❌ Infer implicit requirements not stated in the spec

### Rule 1: Inline library API patterns

Forge will guess library APIs and get details wrong. If a ticket uses multer, ws, express middleware, or any non-trivial API, show the exact pattern:

```
// BAD: "Use multer for file upload"
// Forge writes: multer({ memoryStorage() }) — wrong API

// GOOD: "Use multer with this pattern:
//   const upload = multer({ storage: multer.memoryStorage(), limits: { fileSize: 10_000_000 } })
//   router.post('/voice', upload.single('audio'), async (req, res) => { ... })"
```

This doesn't mean writing the whole file for Forge. It means showing the 2-3 lines where the API is non-obvious.

### Rule 2: Be explicit about data flow

Every variable that comes from user input, config, or another service must be explicitly traced:

```
// BAD: "Send the mode to the LLM"
// Forge hardcodes 'txt2img' or pulls it from the wrong place

// GOOD: "Read mode from req.body.mode (string). Validate it's one of: 'txt2img', 'img2img', 'img2video', 'txt2music'.
//        Pass mode to chatWithRemy(messages, mode) as the second argument."
```

### Rule 3: Every ticket ends with build + runtime verification

Forge's last step in every ticket must be:
1. Run the build command (`npx vite build` / `ruff check` / equivalent)
2. If build fails, fix errors and retry
3. Start the server with mocks: `REMY_CONFIG=remy.config.mock.json npx tsx src/server/index.ts`
4. Run the smoke test curl command
5. Report build result AND runtime result

Build alone is not sufficient. Vite's bundler tolerates syntax that tsx's runtime parser rejects. A file that builds may crash at runtime.

### Rule 4: Max 3 context files

Forge reads and integrates 2-3 context files reliably. At 5+ files, it spends too much time reading and runs out of context for writing. If a ticket genuinely needs more context, inline the critical parts (type definitions, interface shapes) directly in the spec text instead of adding more files to read.

### Rule 5: Only new files in required_output_files

`required_output_files` must contain only files Forge **creates**, not files it **modifies**. The dispatch checker verifies Forge called `write_file` for each entry — if the file already exists and Forge skips the write call, the dispatch fails even though the file is on disk. Modifications to existing files are verified by the build check instead (missing imports → build failure).

### Rule 6: One owner per shared integration file

Shared integration files — main entry points (`+page.svelte`, `main.py`, `App.tsx`), root layouts, app routers — must NOT be modified by multiple Forge tickets. Each Forge rewrite is a fresh take that loses work from previous tickets. QA checks file existence, not "did you preserve what was already there."

**The pattern:** Forge writes components as isolated files. After all component tickets in a phase land, Pixel writes the integration file that wires them together. This is infrastructure wiring, not app code — same category as `__init__.py` files and package.json.

Alternatively, one dedicated integration ticket at the end of each slice batch handles all the wiring. But never distribute modifications to the same file across multiple Forge tickets.

**What went wrong (Dashboard, 2026-05-06):** Five Phase 2 tickets each rewrote `+page.svelte`. Each rewrite was a fresh take — Forge generated a valid page for its own components but dropped imports and sections from previous tickets. The final file was missing TelemetryPanel, LoopHealth, HumanQueue, DispatchTable, LemonadeLog, and had invented sections not in the spec. All 5 tickets passed QA (file exists, non-empty, build passes with just that ticket's components). Runtime testing in Phase 3 revealed the broken integration.

### Rule 7: Health/connection stores must distinguish reachability from service health

Every connection or health-polling store must track two separate states:
- **Reachable:** Did the HTTP request succeed? (fetch didn't throw)
- **Healthy:** Did the response indicate all services are OK? (response body `ok === true`)

These produce different UI messages:
- Reachable=false → "Backend unreachable — data may be stale"
- Reachable=true, Healthy=false → "Services offline: X, Y" (list the failing services)
- Reachable=true, Healthy=true → no banner

Specs must explicitly define these as separate state fields. Do not conflate them into a single `connected` boolean.

**What went wrong (Dashboard, 2026-05-06):** The connection store set `connected = data.ok`, conflating "backend reachable" with "all services healthy." When a ticket DB was deleted, the health endpoint correctly returned `ok: false` with the specific failing service, but the banner showed "Backend unreachable" instead of "Services offline: test-tickets.db" because the store treated any `ok: false` as a connection failure.

### Rule 8: Inline exact import lines for existing modules

When a ticket references an existing store, service, or utility, inline the exact import statement in the spec. Forge guesses export names from file names and gets them wrong (e.g. `lemonadeLogs` instead of `lemonadeLogStore`). Show the import line explicitly:

```
Import the store like this:
import { lemonadeLogStore } from '$lib/stores/lemonadeLogs';
```

### Rule 9: State that globally-loaded CSS must not be re-imported

When design tokens or global CSS is loaded via a root layout or app.css, every component spec must include: "Design tokens are loaded globally via app.css. Do NOT add any import or @import for design-tokens.css in this component." Forge consistently hallucates CSS import paths when it sees CSS variable references.

### Rule 11 (Visual rewrites): Provide exact script block verbatim

When a ticket asks Forge to rewrite a component visually (change template/style but keep logic), provide the EXACT current `<script>` block verbatim in the spec. Tell Forge explicitly: *"Keep this exact script block. Only change the `<template>` and `<style>` sections."*

Without this, Forge rewrites the logic too. Every time.

### Rule 12: In Svelte templates, every store reference needs the `$` prefix — verify explicitly

Forge consistently drops the `$` reactive prefix on Svelte store references in templates. `{totalScope}` renders the store object (`[object Object]`). `{$totalScope}` renders the value. This happens even when Forge correctly uses `$` elsewhere in the same file.

In every Svelte spec that uses stores, add this explicit instruction:

> *"In the template, every store must be accessed with the `$` prefix: `{$storeName}`, `{#if $storeName > 0}`, `{#each $storeName as item}`, `class:foo={$storeName === 'bar'}`. Do NOT reference a store without `$` in the template — that renders the store object itself, not its value."*

After Forge writes any Svelte component, scan the template for store names imported in the script block and verify each one has `$` in the template.

### Rule 13: For shared stores/utilities, provide the complete current file and mark additions explicitly

When a ticket touches a shared file like `tickets.ts`, `connection.ts`, or any store that other components import — provide the COMPLETE current file content verbatim. Mark exactly what to ADD (with a comment) and what to PRESERVE (everything else).

Do NOT say "add an export at the bottom" without showing the full file. Forge will rewrite the whole file from scratch with its own assumptions about what the module should look like.

Example spec language:
```
## File: src/lib/stores/tickets.ts — ADD ONLY

The current file is shown below. ADD the `activeTicket` export after the last existing export. Do NOT change anything else — not the Ticket interface, not the ticketStore factory, not any existing exports.

[full file content here]
```

### Rule 15: When Forge fails, fix the spec and retry — do not write the code as Pixel

When a ticket hits `execution_failure` or `blocked`, the correct response is:
1. Read the ticket_events log to understand what Forge actually tried
2. Identify which known pitfall applied (wrong paths, clobber, missing file, bad API usage)
3. Update the spec to address the root cause
4. Reset the ticket to `todo` and let Forge retry

**Do not write the code as Pixel.** Writing code directly:
- Masks a spec problem that will recur on the next similar ticket
- Produces work with no evidence trail, no QA, no Forge verification
- Defeats the purpose of testing local model capability

**Exception — Rule 6 wiring:** Shared integration files (`+page.svelte`, `main.py`, `App.tsx`, root layouts) are Pixel's responsibility per Rule 6, not Forge's. After all component tickets in a phase land, Pixel writes the wiring. But even then:
- Verify every behavioral dependency is satisfied before writing (e.g. if wiring adds a reactive store lookup, verify the store is populated)
- Test the integration works end-to-end before marking the phase done
- Document the wiring step in the ticket event log

### Rule 16: Before advancing phases, verify integration dependencies are live

`qa_verified` on individual tickets means the files exist and the build passes — it does not mean the integration works. Before dispatching any Phase N ticket, verify that Phase N-1 outputs it depends on are actually wired and live.

Examples:
- P0 adds `registryPath` to config → before P1 dispatches, verify `GET /api/intake/projects` returns expected data, not an empty list
- P1 adds a Svelte store that reads from an API → before P2 dispatches, open the app and confirm the store populates
- A config change → restart the service and verify the change took effect

If a Phase N-1 output isn't integrated, stop and fix it before Phase N runs. A chain of individually-passing tickets can still produce a broken app if each assumes the prior one's integration was verified.

### Rule 17: Handoffs across phase boundaries must include a risks/watch-for section

When handing off work that crosses a phase boundary (session end, subagent handoff, overnight run), the handoff message must include:
- What phase completed and what's in the next queue
- **Known risks / what to verify in the morning** — specific failure modes to watch for
- Any behavioral changes that depend on runtime state (registry populated, config updated, service restarted)

Happy-path "check this URL" is not enough. If a ticket changed behavior that depends on a new dependency, name the dependency and how to verify it.

### Rule 14: Pre-dispatch git snapshot + file allowlist

Before every Forge dispatch:
1. The executor automatically runs `git add -A && git commit -m "pre-forge: <ticket-id>"` in the deliverable root
2. The engine enforces that Forge can ONLY write files listed in `required_output_files_json` — any other write attempt is blocked and logged

If a dispatch breaks things:
- `git diff HEAD~1` to see exactly what changed
- `git checkout HEAD~1 -- <file>` to restore a specific file
- `git reset --hard HEAD~1` to fully revert (nuclear option)

The git history IS the audit trail. Every pre-forge commit is labeled with the ticket ID.

---

### Rule 10: Ticket verification step

Every ticket must include a concrete verification command in the spec (typically `npm run build`). This is Tier 1 QA — it catches syntax errors and broken imports but NOT runtime rendering bugs.

For broader verification at phase boundaries, run the **manual smoke test** (Tier 2):
```bash
python bumblebee/scripts/smoke_test.py --project <slug>
```
This launches the dev server, checks the page renders, and takes a screenshot. Run it after all tickets in a phase reach `qa_verified`, not per-ticket. See `bumblebee/README.md` → "Manual Smoke Test" for full documentation.

### Rule 10a: Original Rule — Ticket verification step (the per-ticket build check)

Every ticket must include a concrete verification command in the spec. This is not the same as the QA smoke test — this is Forge verifying its own work before reporting done:

```
After writing all files, run:
  cd C:\path\to\project && npx vite build
  REMY_CONFIG=remy.config.mock.json npx tsx src/server/index.ts &
  curl -s http://127.0.0.1:4177/api/remy/chat -X POST -H "Content-Type: application/json" -d '{"message":"test"}'
Report whether build passes AND the curl returns a valid response.
```

---

## State Management

State management must be simple enough for Forge to write correctly. The rule: **if the state pattern can't be expressed as an enum and a switch, it's too complex for one ticket.** Split it.

### Pattern: App-level status context

Each app maintains a single status object tracking connection state and feature states:

```typescript
// Remy example
type AppStatus = {
  lemonade: 'connected' | 'disconnected' | 'checking';
  comfyui: 'connected' | 'disconnected' | 'checking';
  voice: 'idle' | 'recording' | 'transcribing' | 'thinking' | 'speaking';
  generation: 'idle' | 'queued' | 'running' | 'complete' | 'error';
};
```

- **Phase 1 skeleton** creates the context with just connection states.
- **Each vertical slice** adds its feature states (voice, generation, etc.).
- **Global banner** reads connection states; individual components read feature states.
- **No external state machine libraries.** React context (Remy), Svelte stores (Dashboard), Python enum + handler (Conference Analytics).

### Per-project patterns

- **Remy (React):** One React context with AppStatus. Provider at App level, consumed by banner + features. Each slice ticket extends the type.
- **Dashboard (SvelteKit):** Svelte stores are reactive by default. Each SSE stream feeds a store, components subscribe. Dashboard is read-only — it displays state, doesn't transition through it.
- **Conference Analytics (Python):** Vision worker has real lifecycle: `initializing → calibrating → running → error → reconnecting`. Simple Python enum + handler — no library.

---

## Health Check Config

The health check script reads a generic `healthChecks` array from the project config. Each entry declares a check type and the parameters for that type. This schema works for any project — Remy, Dashboard, Conference Analytics, or future projects.

```json
{
  "healthChecks": [
    { "type": "http", "name": "Lemonade", "url": "http://[::1]:13305/v1/models" },
    { "type": "http", "name": "ComfyUI", "url": "http://127.0.0.1:8000/system_stats" },
    { "type": "models", "name": "Required LLM models", "endpoint": "http://[::1]:13305/v1/models", "required": ["qwen3.5-9b-FLM", "Whisper-Large-v3-Turbo", "kokoro-v1"] },
    { "type": "directory", "name": "Media Library", "paths": ["C:\\Media Library\\Pictures"] },
    { "type": "file", "name": "tickets.db", "path": "path/to/tickets.db" },
    { "type": "command", "name": "ONNX Runtime", "command": "python -c \"import onnxruntime\"", "expectExitCode": 0 }
  ]
}
```

### Supported check types

| Type | Parameters | What it checks |
|---|---|---|
| `http` | `url` | HTTP GET returns 2xx or 404 (server reachable) |
| `models` | `endpoint`, `required[]` | GET endpoint returns JSON with `data[].id`, all required IDs present |
| `directory` | `paths[]` | Each path exists and is a directory |
| `file` | `path` | Path exists and is a file |
| `command` | `command`, `expectExitCode` | Run shell command, check exit code |

The health check script (`scripts/health-check.ts`) is shared build-system tooling. It accepts `--config <path>` to point at any project's config file. Projects that need project-specific health logic beyond these types can extend the script or add custom check types.

### Boot guard config

The boot guard reads the same config to know which services to monitor at runtime. Web apps use the `http` entries to build a dynamic service status tracker. Headless workers use them to log structured health output. The service list is never hardcoded in app code.

---

## Mock Services

Mock services are lightweight stubs that return canned responses for every external dependency. They run during development and QA tiers 1–4, eliminating the need for live backends, loaded models, or specialized hardware.

### Design Principles

- **Separate ports from real services.** Mocks bind to adjacent ports (e.g. real Lemonade on 13305, mock on 13306) so both can run simultaneously. Each project has two config files: production (real URLs) and mock (mock URLs). The app loads the appropriate config via env var. This avoids port conflicts that can kill real services during test runs.
- **Static canned responses.** No AI, no inference, no model loading. Just return valid JSON that matches the real API shape.
- **Simulate latency where it matters.** Generation progress should emit SSE events over a few seconds, not instantly — this tests the frontend's progress handling.
- **Realistic edge cases.** Mock data should include boundary values, not just static midpoints. Telemetry mocks should occasionally spike to 100% or drop to 0% to test UI edge handling. A mock that always returns 45.2% NPU utilization never reveals rendering bugs at the extremes.
- **Hardware-accurate latency.** Don't use flat intervals. Simulate real hardware spin-up: a 3-second initial block before the first progress event (model loading onto GPU/NPU), then rapid progress updates once inference starts. This prevents frontends from timing out during the heavy initial compute handoff that happens on real hardware.
- **Zero-state responses.** Every mock must support a "connected but empty" mode: Lemonade running with zero models loaded, ComfyUI running with no workflows, camera connected but returning black frames. Forge needs to know how to render a clean empty state without crashing. This is a distinct failure mode from "disconnected" — the service is reachable, but there's nothing to work with.
- **Error injection.** Each mock accepts an env var (e.g., `MOCK_ERROR_RATE=0.1`) to simulate failures — 500 errors, timeouts, malformed JSON — for resilience testing in Phase 3.
- **Zero-state mode is mandatory.** Every mock must support `MOCK_ZERO_STATE=1`: Lemonade returns empty model list, ComfyUI returns no workflows, camera returns black frames. This tests "connected but nothing to work with" — a distinct failure mode from "disconnected." Phase 0 must include zero-state response files alongside happy-path responses.
- **Latency profiles.** The mock config supports per-route `latencyMs` and WebSocket `initialDelayMs` (simulates model loading onto GPU/NPU before first event). Default WebSocket profile: 3s initial delay, then rapid events. Flat intervals mask real timeout bugs.

### Lemonade Mock Server (common dependency)

Most swarm projects depend on Lemonade. There are two distinct usage patterns, and each needs a different mock surface:

| Pattern | Endpoints used | Example projects | Mock returns |
|---|---|---|---|
| **Telemetry / monitoring** | `/api/v1/stats`, `/api/v1/system-info`, `/v1/models` | Dashboard, future ops tools | Time-varying metrics (TOK/s, NPU util, model list) |
| **Inference** | `/v1/chat/completions`, `/v1/audio/transcriptions`, above + telemetry | Remy, any AI-powered app | Canned chat responses, audio transcription results, plus telemetry |

A project that only reads telemetry (like Dashboard) does not need to mock the inference endpoints. A project that calls the LLM needs both.

For either pattern, the mock must:

- **Actually run as an HTTP server** on the mock port (e.g. 13306). A config entry pointing at a port with nothing listening is not a mock — it's a broken dependency.
- Return time-varying data (sin-wave values) so telemetry UIs can be tested with movement, not flat lines
- `start-mocks` must start this server; `stop-mocks` must kill it
- Boot guard and health check must pass with the mock server running

This is the Phase 0 completeness test: if boot guard reports NOT READY after `start-mocks`, Phase 0 is not done.

### Architecture: Shared Engine, Per-Project Data

**Hybrid approach** — a single shared mock engine with per-project configuration:

```
bumblebee/
  mock-engine/              # Shared — one copy, all projects use it
    server.ts               # Core HTTP/WS server with route loading
    latency.ts              # Latency injection + error simulation
    README.md
  
project-root/
  mocks/
    config.json             # Which endpoints to mock, which port
    responses/              # Per-project canned JSON responses
      lemonade-transcribe.json
      lemonade-chat.json
      comfyui-prompt.json
    data/
      silence.wav           # Canned TTS audio
      placeholder.png       # Canned generation output
    start-mocks.sh          # Starts shared engine with this project's config
```

**Why hybrid:** Lemonade is used by Remy, Dashboard, and potentially future projects. Duplicating the mock server per project creates a maintenance burden if Lemonade's API shape changes. The shared engine handles routing, latency, and error injection. Each project provides only its response data.

### Mock categories

Not all dependencies are network services. The shared mock engine covers HTTP + WebSocket mocks. Other dependency types need different mock strategies:

| Category | Examples | Mock strategy | Managed by |
|---|---|---|---|
| **Network services** | Lemonade API, ComfyUI API, event ingest endpoint | Shared mock engine (config-driven) | `start-mocks` script |
| **System APIs** | Windows WMI, hardware sensors | Env-flag in-process mock (`MOCK_TELEMETRY=1` → code returns static data instead of calling WMI) | App code + `start-mocks` sets env vars |
| **Hardware** | Webcam, microphone, GPU | Env-flag + test fixture (`MOCK_CAMERA=1` → read from looping test video instead of live device) | App code + `start-mocks` sets env vars + test fixtures in `mocks/data/` |
| **Data files** | SQLite DBs, config files, model files | Pre-seeded test fixtures copied into place by `start-mocks` | `start-mocks` script |

**Decision process during Phase 0 decomp:**
1. List every dependency in the manifest
2. Categorize each as network, system API, hardware, or data file
3. Network → add to `mocks/config.json` for the shared engine
4. Non-network → flag in the manifest as needing a custom mock. Pixel designs the mock strategy (env flag, test fixture, or custom stub). Document it in the project's `mocks/README.md`.
5. `start-mocks` script orchestrates ALL mock types — starts the shared engine AND sets env vars AND copies test fixtures
6. `stop-mocks` tears down ALL mock types — kills the engine AND unsets env vars AND optionally cleans fixtures

### Per-Project Mock Inventory

#### Remy — Mock Lemonade
Replaces: `http://[::1]:13305`

| Endpoint | Canned Response |
|---|---|
| `POST /v1/audio/transcriptions` | `{ "text": "make a pixel art cat wearing a tiny hat" }` |
| `POST /v1/chat/completions` | `{ "choices": [{ "message": { "content": "{\"reply\": \"Great idea! I can see a cute pixel cat...\", \"prompt\": \"pixel art cat, tiny hat, 8-bit style, bright colors\"}" }}]}` |
| `POST /v1/audio/speech` | Returns a small valid WAV file (silence, ~1KB) |
| `GET /v1/models` | `{ "data": [{ "id": "qwen3.5-9b-FLM" }, { "id": "Whisper-Large-v3-Turbo" }, { "id": "kokoro-v1" }] }` |
| `GET /v1/stats` | `{ "tokens_per_second": 42, "time_to_first_token": 0.3 }` |

#### Remy — Mock ComfyUI
Replaces: `http://127.0.0.1:8000` + `ws://127.0.0.1:8000/ws`

| Endpoint | Canned Response |
|---|---|
| `POST /prompt` | `{ "prompt_id": "mock-123" }` |
| `GET /ws?clientId={id}` | WebSocket: `execution_start` → 5x `progress` (1s apart) → `executed` (mock output filename) → `execution_success` |
| `GET /history` | Empty history |

Output: mock writes a small placeholder PNG to `C:\Media Library\Pictures\mock-output.png` when generation "completes."

#### Dashboard — Mock Lemonade (telemetry only)
Replaces: `http://[::1]:13305`

| Endpoint | Canned Response |
|---|---|
| `GET /api/v1/stats` | `{ "tokens_per_second": 38.5, "time_to_first_token": 0.28 }` — with periodic spikes/drops |
| `GET /api/v1/system-info` | `{ "devices": { "amd_npu": { "utilization": 45.2 }}}` — varies 0–100% |
| `GET /api/v1/models` | List of loaded models |

#### Dashboard — Mock WMI
Not a network service — mock via environment variable:
- `MOCK_TELEMETRY=1` → `wmi_poller.py` returns varying static JSON instead of running PowerShell
- Includes realistic bounds: CPU 0–100%, RAM within system capacity, GPU util spikes

#### Conference Analytics — Mock Vision Pipeline
- `MOCK_CAMERA=1` → vision worker reads from a looping test video file instead of live webcam
- Emits the same analytics events (person count, dwell time, expression) on a fixed 2-second cycle
- Includes edge cases: 0 faces detected, camera disconnect/reconnect, very high face count

### Starting & Tearing Down Mocks

Each project's `mocks/start-mocks.sh` (or `.ps1` on Windows):
1. Starts the shared mock engine with the project's config
2. Waits for each mock endpoint to respond to a health check
3. Returns exit code 0 only when all mocks are healthy
4. QA pipeline calls this before any tier 3+ test

**Teardown is mandatory.** Each project also has `mocks/stop-mocks.sh` that:
1. Kills all mock processes spawned by start-mocks
2. Frees all bound ports (13305, 8000, etc.)
3. Runs **unconditionally** — on test pass, test fail, script crash, or timeout

The QA pipeline wraps every tier 3+ run in a try/finally that calls stop-mocks. Zombie mock processes locking ports is the #1 cause of "works once, fails on retry" in local QA. The teardown script is a Phase 0 deliverable, tested before any feature tickets are written.

---

## QA Tiers

| Tier | Name | What it checks | When it runs |
|---|---|---|---|
| 1 | Static | Files exist, non-empty, no stubs | After every ticket |
| 2 | Build | `vite build` / `pyright` / equivalent passes | After every ticket |
| 3 | Boot | App starts with mocks (tsx runtime, not just vite build), health endpoint returns 200, no console errors | After every ticket |
| 4 | Smoke | Per-slice curl/fetch tests return expected shapes **at runtime** | After every ticket |
| 5 | Integration | Full user flows with live backends | Per-slice gate |
| 6 | Resilience | Stop each dependency, verify graceful degradation; test zero-state (connected but empty) | Per-phase gate |

Current system only does tiers 1–2. **Tiers 3–4 are where real bugs live** and must run after every ticket.

**Critical lesson (Remy, 2026-05-06):** `vite build` can pass while `tsx` runtime fails. The bundler and the runtime parser have different strictness levels. A ticket that passes tier 2 (build) can fail tier 3 (boot) due to syntax the bundler tolerates but the runtime rejects. **Tier 3 is mandatory, not optional.**

### Stack-specific QA commands

The `qa_cmd_json` field must explicitly define the test environment so the pipeline executes the correct tools:

- **TypeScript/React (Remy):** `vite build` for tier 2, `vitest` for smoke tests
- **Python/FastAPI (Dashboard):** `pyright` or `ruff check` for tier 2, `pytest` for smoke tests
- **Python/ONNX (Conference Analytics):** `ruff check` for tier 2, `pytest` with mock camera for smoke tests

The QA pipeline reads the stack from `project-config.json` and selects the right tool chain. No hardcoded assumptions about JavaScript.

---

## Cross-Project Validation

This process must work for any project the swarm builds, not just Remy.

### Remy (React + Express + local AI services)
- **Phase 0 deps:** Lemonade (3 models), ComfyUI, C:\Media Library dirs
- **Mocks:** Mock Lemonade (HTTP), Mock ComfyUI (HTTP + WebSocket)
- **Vertical slices:** Library browsing → Text chat → Voice → Generation
- **State:** React context with AppStatus enum
- **Connection handling:** App-level banner for Lemonade + ComfyUI status

### Agent Swarm Dashboard (SvelteKit + FastAPI + WMI + SSE)
- **Phase 0 deps:** SQLite ticket DBs, projects.json, Lemonade stats endpoint, Windows WMI
- **Mocks:** Mock WMI (env flag), Mock Lemonade stats, pre-seeded test tickets.db
- **Vertical slices:** KPI board from test DB → Gate progress animates → Telemetry gauges update → SSE ticket stream → Dispatch table
- **State:** Svelte stores fed by SSE streams
- **Connection handling:** Telemetry panel shows "offline" per source; SSE auto-reconnects

### Conference Analytics (Python vision + OpenClaw aggregation + dashboard)
- **Phase 0 deps:** Webcam/test video, ONNX runtime, OpenClaw event ingest
- **Mocks:** Mock camera (looping test video), mock event sink
- **Vertical slices:** Vision detects faces in test video → Events emit → Dashboard shows viewer count → Dwell time accumulates → Cross-station comparison
- **State:** Python enum lifecycle (initializing → running → error → reconnecting)
- **Connection handling:** Vision worker shows "no camera" gracefully; dashboard shows "station offline"

### What This Proves
The phases and ticket structure are stack-agnostic:
- Phase 0 always produces health checks + mocks (whether the deps are Lemonade, WMI, or a webcam)
- Phase 1 always gets the skeleton running without crashes
- Phase 2 always slices vertically, not horizontally
- Mocks always match real API shapes
- QA tiers 3–4 always catch the bugs that tiers 1–2 miss

---

## File Size & Modularity Rule

Local LLMs struggle with generating accurate diffs, regex replacements, or AST manipulation. Forge rewrites entire files — it does not patch them.

**Rule:** If a file is too large to reliably rewrite in one ticket, the ticket should not be "add X to BigFile.tsx." The ticket should be: **"Extract [feature] into a new SmallFile.tsx with [requirements], and update BigFile.tsx to import it."**

Keep files small enough that a full overwrite is cheap and safe. This also produces better modularity as a side effect.

---

## How to Run It

The Bumblebee engine lives at `bumblebee/engine/`. It replaces the old agent-swarm orchestrator loops entirely. **Do not use** `agent-swarm/orchestrator/` scripts (pass1_5, validate_ticket_requirements, loop_coding_worker, handoff_brief, forge_spawn_direct) — those are the old system.

### Engine components

| File | Purpose |
|---|---|
| `engine/state_machine.py` | Declarative states, transitions, guards. Every ticket state change goes through here. |
| `engine/event_log.py` | Append-only audit trail. Every transition = one INSERT. |
| `engine/executor.py` | Single-cycle sequential executor. ROUTE → DISPATCH → VERIFY → CLEANUP. One process, no orphans. |
| `engine/direct_dispatch.py` | Calls Lemonade API directly with tool-calling (write_file tool). No agent wrapper, no OpenClaw CLI. |
| `engine/config.py` | All paths from `project-config.json`. No hardcoded strings. |
| `engine/qa.py` | Static file checks + build verification. |
| `engine/templates.py` | Scaffold file templates per archetype. |
| `engine/postwrite.py` | BOM stripping, build checks after Forge writes files. |
| `engine/vision.py` | Screenshot-based visual checks (optional). |
| `engine/tests/` | Full test suite — state machine, event log, config, executor, dispatch, QA, integration. |

### Setting up a new project

1. Create `bumblebee/projects/<slug>/project-config.json` (see `bumblebee/projects/remy/project-config.json` for reference)
2. Required config fields: `engine_root`, `project_root`, `workspace_root`, `deliverable_root`, `db_path`, `artifacts_dir`, `checks_dir`, `forge_agent`, `models` (`forge`, `vision`), `forge_timeout_seconds`, `cycle_interval_seconds`, `max_dispatch_attempts`, `lemonade_api_url`
3. Create `bumblebee/projects/<slug>/run_executor.py` (see `bumblebee/projects/remy/run_executor.py` for reference)
4. The engine creates the DB schema automatically on first run

### Running the executor

```python
# From bumblebee/projects/<slug>/run_executor.py
from bumblebee.engine.executor import Executor
from bumblebee.engine.state_machine import StateMachine
from bumblebee.engine.event_log import EventLog
from bumblebee.engine.config import load_config

config = load_config('project-config.json')
conn = sqlite3.connect(str(config.db_path))
sm = StateMachine()
ev = EventLog(conn)
ex = Executor(config, sm, conn, ev)
results = ex.run_loop(max_cycles=100)
```

The executor:
- Reads tickets from the DB
- Routes them through the state machine (todo → in_progress → done → qa_verified)
- Dispatches coding work directly to Lemonade via `direct_dispatch.py`
- Runs QA checks after each dispatch
- Logs every transition to the event log
- Cleans up child processes after each cycle

### Dispatch mechanism

**Direct to Lemonade.** `direct_dispatch.py` calls `http://[::1]:13305/api/v1/chat/completions` with tool-calling enabled. The model gets a `write_file` tool and the ticket spec as the prompt. No `openclaw agent`, no `forge_spawn_direct`, no coding_queue.

### Ticket state machine

Declared in `state_machine.py`. States: `todo`, `in_progress`, `blocked`, `done`, `qa_verified`, `human_review`. Every transition has guards. Undefined transitions raise `InvalidTransition`. Blocked reason codes have routing rules (retry, dispatch to Forge, route to pixel-review, or require human).

### Dashboard integration

The dashboard reads from the same `tickets.db` that the engine writes to. Tickets are created at decomp time so the dashboard shows total scope. As the executor advances tickets, the dashboard reflects progress in real time.

### Dashboard service (production)

- **URL:** `http://localhost:8765` — serves API + built SvelteKit frontend (single process, no Vite)
- **Config:** `dashboard.config.bumblebee.json`
- **Scheduled Task:** `AgentSwarm-Dashboard` — starts at logon, restart-on-failure 5x at 1 min interval
- **Launch script:** `scripts/start-hidden.vbs` → `scripts/start.ps1` → `python -m uvicorn dashboard-api.main:app`
- **No terminal window** — runs fully hidden via wscript.exe wrapper
- **Deliverable root:** `<your-deliverable-root>`

To restart:
```powershell
Stop-ScheduledTask -TaskName 'AgentSwarm-Dashboard'
Start-ScheduledTask -TaskName 'AgentSwarm-Dashboard'
```

To rebuild frontend after code changes:
```powershell
cd <your-deliverable-root>
.\scripts\build.ps1
Stop-ScheduledTask -TaskName 'AgentSwarm-Dashboard'
Start-ScheduledTask -TaskName 'AgentSwarm-Dashboard'
```

---

## Roles

- **Pixel** decomposes the PRD into vertical slices and writes the tickets with acceptance tests, error handling requirements, and context file lists.
- **Root (Pippin)** validates the tickets and acceptance tests against the system architecture before Forge sees them. Architectural gatekeeper — prevents Forge from hallucinating an entire slice based on a poorly scoped ticket.
- **Forge (local model via Lemonade)** executes tickets — writes files, verifies builds, runs smoke tests. Capable of complex integration code (WebSocket, SSE, React context) when specs are precise. Cannot be trusted with architectural decisions, library API guessing, or implicit requirements. Specs must inline API patterns and trace data flow explicitly.
- **QA (executor pipeline)** runs the tiered checks after each ticket. Stops the line on failure.

---

## Next Steps

1. ~~Pippin reviews rev 1~~ ✅
2. ~~Incorporate feedback into rev 2~~ ✅
3. ~~Root review of rev 2~~ ✅ Feedback incorporated into rev 3
4. ~~Root reviews rev 3~~ ✅ Final refinements incorporated — **document approved**
5. ~~Build the shared mock engine + teardown scripts~~ ✅ Phase 0 complete for Remy
6. ~~Cross-project review of Phase 0 artifacts~~ ✅ Health check + boot guard made config-driven; mock categories + gate variants documented
7. ~~Forge capability testing~~ ✅ Test matrix completed (see `bumblebee/FORGE-TEST-RESULTS.md`). Key finding: Forge handles 1-8 file tickets with 2-3 context files when specs are precise. Fails on implicit API details and build-only verification. Process updated with spec rules and mandatory runtime tests.
8. Dashboard as first full Bumblebee + Forge pipeline test
9. If Dashboard succeeds, cut production swarm over to Bumblebee process
