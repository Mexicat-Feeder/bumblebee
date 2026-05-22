# Bumblebee

An automated coding engine. Describe what you want to build, and Bumblebee breaks it into tickets, sends them to an AI model, verifies the output, and retries failures — automatically.

**You provide:** a project description (PRD) and an AI API key.
**Bumblebee does:** ticket decomposition → code generation → verification → retry loop.

## Quick Install (Windows)

Open PowerShell as Administrator and run:

```powershell
irm https://raw.githubusercontent.com/mexicatfeeder-code/bumblebee/master/install.ps1 | iex
```

This will:
1. Install Python and Node.js if needed
2. Clone the repo and build the dashboard
3. Start the dashboard at `http://localhost:8765`
4. Register it as a service that starts automatically

### Manual Install

```bash
git clone https://github.com/mexicatfeeder-code/bumblebee.git
cd bumblebee
pip install -r requirements.txt
pip install -r dashboard/api/requirements.txt
cd dashboard/ui && npm install && npm run build && cd ../..
```

Start the dashboard:

```bash
cd dashboard
python -m uvicorn api.main:app --host 0.0.0.0 --port 8765
```

Open `http://localhost:8765` in your browser.

## Your First Project

### 1. Open the Dashboard

Navigate to `http://localhost:8765`. You'll see the project intake form.

### 2. Create a Project

Fill in:
- **Project Name** — what you're building
- **Description** — one-line summary
- **Code Folder** — where the generated code will live

### 3. Upload Your PRD

Upload a markdown file or paste your product requirements document. This describes what you want built — features, UI, behavior, constraints.

### 4. Configure AI

The dashboard has an **AI Configuration** panel with three model slots:

| Phase | What it does | Recommended |
|---|---|---|
| **Q&A** | Asks clarifying questions about your PRD | Local AI or any model |
| **Decomposition** | Breaks PRD into tickets | Local AI or any model |
| **Coding** | Writes the actual code | Best model available (GPT-4o, Claude, etc.) |

**Using a cloud API (OpenAI, Google, etc.):**
1. Set the phase to "Cloud / Custom API"
2. Enter your API base URL (e.g. `https://api.openai.com/v1`)
3. Enter your API key
4. Enter the model name (e.g. `gpt-4o`)

**Using a local AI (Lemonade, Ollama, etc.):**
If you have a local AI server running that speaks the OpenAI API format (`/v1/chat/completions`), Bumblebee will detect it automatically. The model must support **tool calling** (function calling) for the coding phase.

### 5. Q&A Chat

Click **Start Q&A Chat**. The AI reads your PRD and asks clarifying questions:
- What tech stack should this use?
- What port should the app run on?
- What's the simplest version that counts as done?

Answer the questions. When you've covered enough, click **Finish Q&A**. The AI produces a summary of decisions.

### 6. Decompose

Click **Decompose into Tickets**. The AI analyzes your PRD and Q&A summary, then generates a structured ticket plan:
- **Phase 0**: Base components, config files, shared types
- **Phase 1+**: Features, each as a self-contained ticket

Review the plan. Click **Approve & Create Tickets** to commit.

### 7. Start Coding

Click **Start Coding**. The engine begins processing tickets:
- Sends each ticket to the AI with a `write_file` tool
- Verifies the output files exist and the project builds
- Retries failures automatically (up to 3 attempts)
- Advances through phases as dependencies are satisfied

Watch progress in the dashboard — ticket status, phase completion, and live logs.

## How It Works

### The Engine

Each cycle:
1. **Route** — advance tickets whose dependencies are satisfied
2. **Dispatch** — send one ticket to the AI via tool-calling API
3. **Verify** — check output files exist and project builds
4. **Cleanup** — kill child processes from this cycle

### State Machine

```
todo → in_progress → done → qa_verified (terminal)
         ↓
       blocked (retry / human_review)
         ↓
       back to in_progress (auto-retry)
```

### File Safety

- The AI can only write files listed in the ticket spec (allowlisted)
- Every dispatch is preceded by a git commit for easy rollback
- Build verification runs after every file write

### Two-Model Architecture

Bumblebee was designed around a key insight: **local AI models write correct single-file code but fail at multi-file coordination.** The solution:

- **Decomposition** breaks work into one-file-at-a-time tickets
- **Coding** sends each ticket individually — the model only needs to write 1-3 files
- **Verification** catches errors that the model misses

This means you can use a smaller/cheaper model for Q&A and decomposition, and a more capable model for the actual coding — or run everything locally if your hardware supports it.

## Project Structure

```
bumblebee/
├── engine/                 # Core engine (Python, no external deps)
│   ├── executor.py         # Main execution loop
│   ├── direct_dispatch.py  # AI API communication
│   ├── state_machine.py    # Ticket state transitions
│   ├── qa.py               # Build verification
│   └── config.py           # Project configuration
├── dashboard/              # Web UI (SvelteKit + FastAPI)
│   ├── api/                # Python backend
│   └── ui/                 # Svelte frontend
├── scripts/                # Project setup & decomposition
│   ├── new_project.py      # Create project scaffold
│   └── decompose.py        # PRD → ticket plan
├── projects/               # Your projects live here
├── install.ps1             # One-command installer
└── SPEC-RULES.md           # Guide for writing good ticket specs
```

## Requirements

- **Python 3.11+**
- **Node.js 18+** (for dashboard and frontend projects)
- **An OpenAI-compatible API endpoint** — any of:
  - OpenAI (`https://api.openai.com/v1`)
  - Google Gemini (`https://generativelanguage.googleapis.com/v1beta/openai`)
  - Anthropic (via proxy)
  - A local model server (Ollama, LM Studio, vLLM, llama.cpp, Lemonade)
  - Any provider that speaks `/v1/chat/completions` with tool-calling

The coding model **must support tool calling** (function calling). The engine gives the model a `write_file` tool and expects it to use it.

## Configuration

### Dashboard Config (`dashboard/dashboard.config.json`)

```json
{
  "ticketDbPaths": {},
  "apiPort": 8765,
  "workspaceRoot": "C:\\path\\to\\bumblebee",
  "ai": {
    "lemonade_url": "http://[::1]:13305",
    "qa_model_source": "lemonade",
    "qa_model_id": "Qwen3.6-27B-GGUF",
    "decomp_model_source": "lemonade",
    "decomp_model_id": "Qwen3.6-27B-GGUF",
    "forge_model_source": "custom",
    "forge_model_id": "gpt-4o",
    "custom_api_base_url": "https://api.openai.com/v1",
    "custom_api_key": "sk-..."
  }
}
```

### Project Config (`projects/<slug>/project-config.json`)

Each project gets its own config with paths, model settings, and build commands. Created automatically during decomposition.

### Environment Variables

| Variable | Purpose | Default |
|---|---|---|
| `BUMBLEBEE_API_KEY` | API key for the coding model | *(none)* |
| `BUMBLEBEE_API_BASE_URL` | API endpoint | `https://api.openai.com/v1` |
| `OPENAI_API_KEY` | Fallback API key | *(none)* |
| `DASHBOARD_CONFIG` | Path to dashboard config | `dashboard.config.json` |

## CLI Usage

You can also use Bumblebee without the dashboard:

### Create a project

```bash
python -m bumblebee.scripts.new_project \
  --slug my-app \
  --name "My App" \
  --deliverable-root ./output/my-app \
  --tech-stack "TypeScript/React"
```

### Run the executor

```bash
cd projects/my-app
python run_executor.py
```

## Troubleshooting

### "AI model returned 401"
Your API key is invalid or expired. Check the key in AI Configuration or the `BUMBLEBEE_API_KEY` environment variable.

### "AI model returned no choices"
The model didn't respond. This usually means the model is overloaded or the request timed out. Try again, or switch to a different model.

### "No Q&A model configured"
You haven't selected a model for the Q&A phase. Open AI Configuration in the dashboard and select a model (or set it to "Cloud / Custom API" and enter your API details).

### Dashboard won't start
- Check that Python 3.11+ is installed: `python --version`
- Check that dependencies are installed: `pip install -r dashboard/api/requirements.txt`
- Check that the frontend is built: `ls dashboard/ui/build`
- Try running manually: `cd dashboard && python -m uvicorn api.main:app --port 8765`

### Tickets keep failing
- Check the executor logs in the dashboard (click "Show Logs")
- Common causes: model doesn't support tool calling, API rate limits, invalid API key
- The engine retries up to 3 times per ticket before marking it as blocked

### Local AI not detected
Bumblebee looks for a local AI server at `http://[::1]:13305`. If your server is at a different address, update the Lemonade URL in the dashboard config.

## Writing Good PRDs

The better your PRD, the better the decomposition. Include:

- **What the app does** — features, user flows, expected behavior
- **Tech preferences** — language, framework, or "you decide"
- **UI description** — what the user sees, how they interact
- **Error handling** — what happens when things go wrong
- **Scope boundaries** — what's in v1, what's not

You don't need to specify file structure, architecture, or implementation details — the decomposer handles that.

## License

MIT
