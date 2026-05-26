# Conference Demo — Prep Plan

**Deadline:** 2026-05-27 (install-ready for testing on fresh system)
**Show date:** Week of 2026-06-01
**Target:** Fresh Windows install on Ryzen AI Max system

## What the demo shows
1. **Dashboard alive** — tickets moving through gates, hardware/AI telemetry updating live
2. **Local AI coding** — Forge (Qwen3-Coder via Lemonade) building a real app from tickets
3. **Cost comparison** — tab showing "cloud would cost $X, local cost $0, you saved $X"
4. **Finished app** — food cart ordering app running (optional, if audience wants to see output)

## Demo flow (~5 min)
1. Open dashboard → show completed food-cart project (24 tickets, all verified)
2. Flip to cost comparison tab → show cloud vs local savings
3. Reset demo → re-seed a few tickets → start executor
4. Watch tickets dispatch to Forge, QA run, gates advance — live
5. Show hardware panel (CPU/GPU/NPU utilization while coding)

## Components

### Already done
- [x] Dashboard (SvelteKit + FastAPI) in `bumblebee/dashboard/`
- [x] Engine (executor, state machine, dispatch) in `bumblebee/engine/`
- [x] `install.ps1` — clones repo, installs Python/Node, builds dashboard, registers service
- [x] Food-cart project — 24 tickets across 5 gates, all qa_verified
- [x] Stock-demo project — 11 tickets, all qa_verified
- [x] PixelActivity panel — cloud AI cost/token tracking
- [x] LocalAIPanel — Lemonade model/throughput/token tracking
- [x] HardwarePanel — CPU, RAM, GPU, VRAM, NPU, temp
- [x] Mock telemetry mode (`MOCK_TELEMETRY=1`)

### To build
- [ ] **CostComparison tab** — new Svelte component + API endpoint. Shows side-by-side cloud vs local with savings headline. Separate sidebar tab.
- [ ] **Demo launcher** (`demo.ps1`) — resets food-cart DB to partial state, starts dashboard, starts executor. One command.
- [ ] **Portable food-cart seed** — remove hardcoded `C:\Users\rad_t` paths from seed script
- [ ] **Demo reset script** — re-seeds DB to "gate 1-2 done, gate 3 in progress" state for live demo
- [ ] **install.ps1 polish** — verify works on fresh system, add Lemonade download step
- [ ] **README update** — conference-friendly quick start

### Nice to have
- [ ] Demo project with fewer tickets (5-6) for faster live run
- [ ] "Presentation mode" (PresentationMode.svelte exists — verify it works)
- [ ] Pre-recorded fallback video if live demo fails

## Architecture notes
- Dashboard in bumblebee repo: `dashboard/api/` (FastAPI) + `dashboard/ui/` (SvelteKit)
- Config: `dashboard/dashboard.config.json` — maps project slugs to ticket DB paths
- Engine config: `projects/<slug>/project-config.json` — per-project settings
- Lemonade: `http://[::1]:13305` — local AI server, health at `/api/v1/health`
- Cost data: PixelActivity gets from `/api/pixel-stats` (OpenClaw gateway). For demo, need accumulated token counts per project from ticket artifacts.

## Cost comparison data model
Each completed ticket has a worker artifact (e.g. `artifacts/FC-P1-001.worker.json`) that contains token usage. Sum across all tickets for project totals. Apply cloud pricing (Claude Opus input: $15/M, output: $75/M; GPT-4o input: $2.50/M, output: $10/M) vs local ($0).

## Files modified
Track here for cross-session continuity:
- `dashboard/ui/src/lib/components/CostComparison.svelte` — NEW
- `dashboard/ui/src/lib/stores/costs.ts` — NEW
- `dashboard/ui/src/lib/components/Sidebar.svelte` — add Cost tab
- `dashboard/ui/src/routes/+page.svelte` — wire Cost view
- `dashboard/api/routers/costs.py` — NEW API endpoint
- `projects/food-cart/seed_tickets.py` — make portable
- `demo.ps1` — NEW launcher
- `CONFERENCE-DEMO.md` — this file
