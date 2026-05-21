# Bumblebee

An automated coding engine that decomposes software projects into tickets and dispatches them to an AI model for implementation, with built-in QA and retry logic.

**How it works:** You describe a project → Bumblebee breaks it into phased tickets → an AI model writes the code via tool-calling → the engine verifies each file, runs build checks, and retries failures automatically.

## What You Need

- **Python 3.11+**
- **An OpenAI-compatible API endpoint** — any of:
  - OpenAI (`https://api.openai.com/v1`)
  - Google Gemini (`https://generativelanguage.googleapis.com/v1beta/openai`)
  - A local model server (Ollama, LM Studio, vLLM, llama.cpp, Lemonade)
  - Any provider that speaks `/v1/chat/completions` with tool-calling
- **Node.js** (if building frontend projects — for `npm run dev`, `vite build`, etc.)

The model must support **tool calling** (function calling). The engine gives the model a `write_file` tool and expects it to use it.

## Quick Start

### 1. Set your API key

```bash
export BUMBLEBEE_API_KEY="sk-..."        # or OPENAI_API_KEY
export BUMBLEBEE_API_BASE_URL="https://api.openai.com/v1"  # optional, defaults to OpenAI
```

### 2. Create a project

```bash
python -m bumblebee.scripts.new_project \
  --slug my-app \
  --name "My App" \
  --deliverable-root ./output/my-app \
  --tech-stack "TypeScript/React" \
  --port 3000
```

This creates `projects/my-app/` with a `project-config.json` and `run_executor.py`.

### 3. Configure the model

Edit `projects/my-app/project-config.json`:

```json
{
  "api_base_url": "https://api.openai.com/v1",
  "api_key": "",
  "models": {
    "forge": "gpt-4o",
    "vision": "gpt-4o"
  }
}
```

Leave `api_key` empty to use the `BUMBLEBEE_API_KEY` / `OPENAI_API_KEY` env var.

### 4. Seed tickets

Write a seed script that inserts tickets into the SQLite database. Each ticket needs:
- An **objective** (what to build)
- **Output files** (what files the model must create)
- A **gate** (phase number for ordering)
- **Dependencies** (which tickets must complete first)

See [Ticket Structure](#ticket-structure) below.

### 5. Run

```bash
cd projects/my-app
python run_executor.py
```

The engine loops through tickets: dispatches them to the AI, verifies the output, retries on failure, and advances through the state machine.

## Architecture

```
bumblebee/
├── engine/                     # Core engine (pure Python, no external deps)
│   ├── config.py               # Project config loader
│   ├── state_machine.py        # Declarative states + transitions
│   ├── event_log.py            # Append-only audit trail + DB schema
│   ├── executor.py             # Single-cycle sequential executor
│   ├── direct_dispatch.py      # Sends tasks to AI via OpenAI-compatible API
│   ├── qa.py                   # Static file checks + build verification
│   ├── postwrite.py            # Post-write cleanup (BOM strip, build check)
│   ├── guardrails.py           # Auto-detect common model mistakes
│   ├── vision.py               # Screenshot-based visual QA (optional)
│   ├── screenshot.py           # App launch + screenshot capture
│   ├── templates.py            # Scaffold templates per archetype
│   └── tests/                  # Test suite
├── scripts/
│   ├── new_project.py          # Create a new project
│   ├── decompose.py            # Decompose a PRD into tickets
│   ├── classify_archetype.py   # Classify project type
│   ├── generate_checks.py      # Generate QA check scripts
│   └── smoke_test.py           # Manual smoke test (launch app + screenshot)
├── DECOMPOSITION-PROCESS.md    # How to structure tickets and phases
└── SPEC-RULES.md               # Rules for writing good ticket specs
```

### The Loop

Each executor cycle:

1. **ROUTE** — advance tickets whose dependencies are satisfied
2. **DISPATCH** — send one ticket to the AI model via tool-calling API
3. **VERIFY** — check that required files exist and the project builds
4. **CLEANUP** — kill any child processes spawned during the cycle

### State Machine

```
todo → in_progress → done → qa_verified (terminal)
         ↓
       blocked (retry / coding / human_review)
         ↓
       back to in_progress (auto-retry)
```

Every transition is declared in `state_machine.py` with guards, side effects, and actor constraints. Invalid transitions raise exceptions. No ticket silently rots.

### Direct Dispatch

The engine sends a minimal prompt to the AI:

```
System: You are a code generator. Use write_file to create files.
User: Write these files: [list]. Task: [objective]. Rules: [constraints].
Tools: [write_file(path, content)]
```

The model calls `write_file` for each file. The engine executes the tool calls (writes to disk), then verifies. **File writes are allowlisted** — the model can only write to paths listed in the ticket spec.

## Ticket Structure

Tickets live in a SQLite database. The schema:

```sql
-- Created by init_db()
CREATE TABLE tickets (
    id TEXT PRIMARY KEY,
    owner TEXT,          -- lane/category
    gate INTEGER,        -- phase number (0, 1, 2...)
    status TEXT,         -- todo, in_progress, done, qa_verified, blocked
    depends_on TEXT,     -- JSON array of ticket IDs
    -- ... plus metadata, timestamps, failure counts
);

CREATE TABLE ticket_requirements (
    ticket_id TEXT PRIMARY KEY,
    ticket_description TEXT,           -- full task spec for the AI
    required_output_files_json TEXT,   -- JSON array of relative file paths
    qa_cmd_json TEXT,                  -- JSON array: build/test command
    -- ... plus optional fields
);
```

### Example Seed Script

```python
import json, sqlite3, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from bumblebee.engine.event_log import init_db

conn = sqlite3.connect("tickets.db")
conn.row_factory = sqlite3.Row
init_db(conn)

tickets = [
    {
        "id": "TKT-001",
        "gate": 0,
        "owner": "frontend",
        "description": "Create a Button component with primary and secondary variants...",
        "files": ["src/components/Button.tsx", "src/components/Button.css"],
        "depends_on": [],
    },
    {
        "id": "TKT-002",
        "gate": 0,
        "owner": "frontend",
        "description": "Create a Card component with title, body, and optional footer...",
        "files": ["src/components/Card.tsx", "src/components/Card.css"],
        "depends_on": [],
    },
    {
        "id": "TKT-003",
        "gate": 1,
        "owner": "frontend",
        "description": "Create the main App layout using Button and Card...",
        "files": ["src/App.tsx"],
        "depends_on": ["TKT-001", "TKT-002"],
    },
]

for t in tickets:
    conn.execute(
        "INSERT INTO tickets (id, owner, gate, status, depends_on) VALUES (?, ?, ?, 'todo', ?)",
        (t["id"], t["owner"], t["gate"], json.dumps(t["depends_on"])),
    )
    conn.execute(
        "INSERT INTO ticket_requirements (ticket_id, ticket_description, required_output_files_json) VALUES (?, ?, ?)",
        (t["id"], t["description"], json.dumps(t["files"])),
    )

conn.commit()
print(f"Seeded {len(tickets)} tickets")
```

## Project Config

`project-config.json` — all paths and settings for one project:

```json
{
  "engine_root": "./engine",
  "project_root": ".",
  "workspace_root": "..",
  "deliverable_root": "./output",
  "db_path": "./tickets.db",
  "artifacts_dir": "./output/artifacts",
  "checks_dir": "./output/checks",

  "api_base_url": "https://api.openai.com/v1",
  "api_key": "",

  "forge_agent": "forge",
  "models": {
    "forge": "gpt-4o",
    "vision": "gpt-4o"
  },

  "forge_timeout_seconds": 300,
  "cycle_interval_seconds": 2,
  "max_dispatch_attempts": 3,

  "tech_stack": "TypeScript/React",
  "ui_check": {
    "launch_cmd": ["npm", "run", "dev"],
    "cwd": "./output",
    "url": "http://127.0.0.1:3000",
    "ui_port": 3000
  }
}
```

### Config Resolution Order

For API connection:
1. `api_base_url` in config → 2. `BUMBLEBEE_API_BASE_URL` env → 3. `https://api.openai.com/v1`
1. `api_key` in config → 2. `BUMBLEBEE_API_KEY` env → 3. `OPENAI_API_KEY` env

## Writing Good Specs

The quality of the AI output depends heavily on the ticket spec. See `SPEC-RULES.md` for the full guide. Key principles:

- **One ticket = one concern.** Don't combine "create Button component" with "wire it into App layout."
- **List exact output files.** The engine enforces an allowlist — the model can only write what you specify.
- **Inline architecture rules.** Don't say "follow ARCHITECTURE.md." Paste the relevant rules into the spec.
- **Provide context files verbatim.** If the ticket modifies or integrates with existing code, include the full current file content in the spec.
- **Be explicit about patterns.** "Use `export default function Button()`" beats "export the component."

## QA Tiers

1. **Static** (automatic) — Do required files exist? Are they non-empty? No syntax errors?
2. **Build** (automatic) — Does the project build? (`vite build`, `tsc`, etc.)
3. **Smoke test** (manual) — Launch the app, check it renders, take a screenshot.
4. **Vision** (optional) — Send a screenshot to a vision model for visual verification.

Tiers 1–2 run automatically per ticket. Tier 3 runs manually at phase boundaries via `smoke_test.py`. Tier 4 requires a vision-capable model.

## Guardrails

The engine auto-detects common model mistakes:

- **Svelte `$` prefix** — Detects store references missing `$` in templates
- **Export integrity** — Captures baseline exports before dispatch, fails if exports disappear
- **Rewrite detection** — Flags >60% file deletion as suspicious
- **Allowlist enforcement** — Blocks writes to files not in the ticket spec

## Tips

- **Start with Gate 0.** Base components with zero dependencies. Let the model warm up on simple tasks.
- **Phase boundaries are checkpoints.** Run `smoke_test.py` before moving to the next phase.
- **Git your deliverable root.** The executor auto-commits before each dispatch for easy rollback.
- **Small models work for simple tickets.** Gate 0 components often succeed with smaller/cheaper models. Save the big model for integration tickets.
- **When a ticket keeps failing, fix the spec.** Don't patch the code manually — improve the description, add more context, or split the ticket smaller.

## License

MIT
