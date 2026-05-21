# Bumblebee Spec Rules — Mandatory Pre-Authoring Reference

**Read this file before writing or editing any Forge ticket specs.**
Source: `bumblebee/DECOMPOSITION-PROCESS.md` (full context, read at Phase 0).

---

## Rule 1: Inline library API patterns

Forge guesses library APIs and gets details wrong. Show the exact 2-3 lines where the API is non-obvious.

```
// BAD: "Use multer for file upload"
// GOOD: Show the exact multer({ storage: multer.memoryStorage(), ... }) pattern
```

## Rule 2: Be explicit about data flow

Every variable from user input, config, or another service must be explicitly traced. Don't say "send the mode to the LLM" — say "read mode from req.body.mode (string), validate it's one of [X, Y, Z], pass to fn() as second argument."

## Rule 3: Every ticket ends with build + runtime verification

Build alone is NOT sufficient. `vite build` passes where `tsx` runtime rejects. Forge's last step: build → start server with mocks → run smoke test curl → report both results.

## Rule 4: Max 3 context files

Forge integrates 2-3 context files reliably. At 5+, it reads too much and writes too little. If more context is needed, inline the critical parts (types, interfaces) directly in the spec.

## Rule 5: Only NEW files in required_output_files ⚠️

`required_output_files` must contain only files Forge **creates**, not files it **modifies**. If the file already exists on disk, do NOT list it. Forge gets zero tool calls trying to juggle new files + existing file edits — this is the #1 cause of blocked tickets.

Modifications to existing files are verified by the build check instead (missing imports → build failure).

## Rule 6: One owner per shared integration file ⚠️

Shared integration files (`+page.svelte`, `main.py`, `App.tsx`, root layouts, IntakeView.svelte, Sidebar.svelte) must NOT appear in multiple tickets' `required_output_files`. Each Forge rewrite is a fresh take that drops everything from prior tickets.

**The pattern:** Forge writes components as isolated files. After all component tickets in a phase land, **Pixel writes the integration file** that wires them together. Never distribute modifications to the same file across multiple Forge tickets.

**War story (Dashboard S1):** Five Phase 2 tickets each rewrote `+page.svelte`. Each was valid in isolation but dropped imports from other tickets. Runtime was broken.

**War story (Dashboard S2):** P2-003 through P2-006 each rewrote `IntakeView.svelte`. Final version was missing 4 of 7 components. Sidebar.svelte was also clobbered.

## Rule 7: Health/connection stores — reachable vs healthy

Track two separate states: reachable (fetch succeeded?) and healthy (response says ok?). These produce different UI messages. Never conflate into a single boolean.

## Rule 8: Inline exact import lines

When referencing an existing store/service, show the exact import statement. Forge guesses export names from file names and gets them wrong.

## Rule 9: State that globally-loaded CSS must NOT be re-imported ⚠️

When design tokens or global CSS is loaded via a root layout, every component spec must say: "Design tokens are loaded globally. Do NOT add any import for design-tokens.css."

Forge hallucates CSS import paths every time it sees CSS variable references. Every Forge-written component in Dashboard S2 had wrong paths.

## Rule 10: Ticket verification step

Every ticket includes a concrete verification command (typically `npm run build`). This is Tier 1 QA. For broader verification at phase boundaries, run the manual smoke test (`python bumblebee/scripts/smoke_test.py --project <slug>`).

## Rule 11: Visual rewrites — provide exact script block

When rewriting a component visually (template/style only), provide the exact current `<script>` block verbatim. Tell Forge: "Keep this exact script block. Only change template and style." Without this, Forge rewrites the logic too.

## Rule 12: Svelte store `$` prefix — verify explicitly ⚠️

Forge consistently drops `$` on Svelte store refs in templates. Add this instruction to every Svelte spec using stores:

> "In the template, every store must use the `$` prefix: `{$storeName}`, `{#if $storeName > 0}`. Do NOT reference a store without `$` in the template."

After Forge writes any Svelte component, scan for store names and verify `$` prefix.

## Rule 13: Shared stores/utilities — provide full file, mark additions

Provide the COMPLETE current file verbatim. Mark exactly what to ADD and what to PRESERVE. Do NOT say "add an export at the bottom" without showing the full file — Forge will rewrite the whole file from scratch.

## Rule 14: Pre-dispatch git snapshot + file allowlist

Before every dispatch, the executor auto-commits in the deliverable root. The engine blocks writes outside `required_output_files_json`. If a dispatch breaks things: `git diff HEAD~1` or `git checkout HEAD~1 -- <file>`.

## Rule 15: Forge fails → fix spec → retry. Never write code as Pixel. ⚠️

Read ticket_events → identify the pitfall → update spec → reset to todo. Writing code directly masks spec problems that recur on the next ticket.

**Exception:** Rule 6 wiring (shared integration files) is Pixel's job after component tickets land. But verify integration before marking done.

## Rule 16: Before advancing phases, verify integration deps are live

`qa_verified` = files exist + build passes. NOT = integration works. Before Phase N, verify Phase N-1 outputs are wired and live. Restart services if config changed. Verify API endpoints return expected data.

## Rule 17: Handoffs must include risks/watch-for

When crossing phase boundaries: what completed, what's next, known risks, behavioral dependencies that need runtime verification.

---

## Quick Checklist (run mentally before seeding tickets)

- [ ] Every `required_output_files_json` entry is a NEW file (Rule 5)
- [ ] No file appears in multiple tickets' output lists (Rule 6)
- [ ] Shared integration files (layouts, routers, main pages) are handled by Pixel wiring, not Forge (Rule 6)
- [ ] Library API patterns are inlined, not assumed (Rule 1)
- [ ] Data flow is explicitly traced (Rule 2)
- [ ] Svelte specs include `$` prefix instruction (Rule 12)
- [ ] CSS import instruction says "do NOT import design-tokens" (Rule 9)
- [ ] Max 3 context files per ticket (Rule 4)
- [ ] Import lines for existing modules are shown verbatim (Rule 8)
