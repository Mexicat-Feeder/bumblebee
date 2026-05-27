"""
research_executor.py — Sift research agent executor loop.

Picks up queued research tickets, calls Lemonade's OpenAI-compatible API
with Sift's personality, writes reports to disk, and marks tickets complete.

Usage:
    python engine/research_executor.py --db-path ./research/research.db --reports-dir ./research/reports
"""
from __future__ import annotations

import argparse
import json
import logging
import signal
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [SIFT] %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger("sift")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LEMONADE_BASE = "http://[::1]:13305"
HEALTH_URL = f"{LEMONADE_BASE}/api/v1/health"
COMPLETIONS_URL = f"{LEMONADE_BASE}/v1/chat/completions"

BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"
BRAVE_KEY_PATH = Path.home() / ".bumblebee" / "brave-api-key.txt"
SEARCH_RESULT_COUNT = 5

SIFT_SYSTEM_PROMPT = """\
You are Sift, a research analyst agent. You investigate topics thoroughly and produce well-structured research reports.

Your reports should include:
- An executive summary (2-3 sentences)
- Key findings organized by theme, referencing sources where provided
- Practical recommendations
- A Sources section listing URLs you referenced

When web search results are provided, use them as your primary source material. Cite specific findings from the search results. If search results are thin, supplement with your own knowledge but note what is from search vs general knowledge.

Write in a clear, direct style. Prefer concrete examples over abstractions. If the topic is technical, include code snippets or configuration examples where relevant.
"""

TEMPERATURE = 0.4
MAX_TOKENS = 4096
SLEEP_SECONDS = 5

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_shutdown = False


def _handle_sigint(sig, frame):  # noqa: ANN001
    global _shutdown
    log.info("Shutdown signal received — finishing current ticket then exiting.")
    _shutdown = True


signal.signal(signal.SIGINT, _handle_sigint)
signal.signal(signal.SIGTERM, _handle_sigint)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=15000")
    return conn


def detect_model() -> str | None:
    """Query Lemonade health endpoint and return the loaded model name."""
    try:
        r = httpx.get(HEALTH_URL, timeout=5.0)
        r.raise_for_status()
        data = r.json()
        return data.get("model_loaded") or None
    except Exception as exc:
        log.warning("Could not reach Lemonade health endpoint: %s", exc)
        return None


def load_brave_key() -> str | None:
    """Read Brave API key from ~/.bumblebee/brave-api-key.txt if it exists."""
    try:
        if BRAVE_KEY_PATH.exists():
            key = BRAVE_KEY_PATH.read_text(encoding="utf-8").strip()
            if key:
                return key
    except Exception:
        pass
    return None


def brave_search(query: str, api_key: str) -> list[dict]:
    """Search Brave and return a list of {title, url, description} results."""
    try:
        r = httpx.get(
            BRAVE_SEARCH_URL,
            params={"q": query, "count": SEARCH_RESULT_COUNT},
            headers={"Accept": "application/json", "X-Subscription-Token": api_key},
            timeout=15.0,
        )
        r.raise_for_status()
        data = r.json()
        results = []
        for item in data.get("web", {}).get("results", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "description": item.get("description", ""),
            })
        return results
    except Exception as exc:
        log.warning("Brave search failed for '%s': %s", query[:60], exc)
        return []


def format_search_context(results: list[dict]) -> str:
    """Format search results into a context block for the LLM prompt."""
    if not results:
        return ""
    lines = ["\n## Web Search Results\n"]
    for i, r in enumerate(results, 1):
        lines.append(f"### [{i}] {r['title']}")
        lines.append(f"URL: {r['url']}")
        lines.append(f"{r['description']}\n")
    return "\n".join(lines)


def call_lemonade(model: str, question: str, search_context: str = "") -> str:
    """Call Lemonade chat completions and return the response text."""
    user_content = question
    if search_context:
        user_content = f"{question}\n{search_context}"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SIFT_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
    }
    # Research calls can take a while — generous timeout
    r = httpx.post(COMPLETIONS_URL, json=payload, timeout=300.0)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"]


# ---------------------------------------------------------------------------
# Executor loop
# ---------------------------------------------------------------------------

def fetch_next_ticket(conn: sqlite3.Connection) -> sqlite3.Row | None:
    """Return the oldest queued ticket, or None."""
    return conn.execute(
        """
        SELECT
            rq.ticket_id,
            rq.queue_status,
            rq.attempt_count,
            tr.ticket_description
        FROM research_queue rq
        JOIN ticket_requirements tr ON tr.ticket_id = rq.ticket_id
        WHERE rq.queue_status = 'queued'
        ORDER BY rq.priority ASC, rq.enqueued_at ASC
        LIMIT 1
        """
    ).fetchone()


def mark_in_progress(conn: sqlite3.Connection, ticket_id: str) -> None:
    ts = now_iso()
    conn.execute(
        "UPDATE research_queue SET queue_status='in_progress', last_attempt_at=? WHERE ticket_id=?",
        (ts, ticket_id),
    )
    conn.execute(
        "UPDATE tickets SET status='in_progress', updated_at=? WHERE id=?",
        (ts, ticket_id),
    )
    conn.execute(
        """INSERT INTO ticket_events (ticket_id, from_status, to_status, actor, timestamp, note)
           VALUES (?, 'queued', 'in_progress', 'sift', ?, 'Research started')""",
        (ticket_id, ts),
    )
    conn.commit()


def mark_complete(conn: sqlite3.Connection, ticket_id: str, report_path: str) -> None:
    ts = now_iso()
    conn.execute(
        """UPDATE research_queue
           SET queue_status='human_acked', report_path=?, last_note='Report delivered', last_attempt_at=?
           WHERE ticket_id=?""",
        (report_path, ts, ticket_id),
    )
    conn.execute(
        "UPDATE tickets SET status='qa_verified', updated_at=? WHERE id=?",
        (ts, ticket_id),
    )
    conn.execute(
        """INSERT INTO ticket_events (ticket_id, from_status, to_status, actor, timestamp, note)
           VALUES (?, 'in_progress', 'qa_verified', 'sift', ?, 'Report written and delivered')""",
        (ticket_id, ts),
    )
    conn.commit()


def mark_failed(conn: sqlite3.Connection, ticket_id: str, error: str) -> None:
    ts = now_iso()
    note = error[:500]  # keep note bounded
    conn.execute(
        """UPDATE research_queue
           SET queue_status='failed', last_note=?,
               attempt_count = attempt_count + 1, last_attempt_at=?
           WHERE ticket_id=?""",
        (note, ts, ticket_id),
    )
    conn.execute(
        "UPDATE tickets SET status='blocked', updated_at=? WHERE id=?",
        (ts, ticket_id),
    )
    conn.execute(
        """INSERT INTO ticket_events (ticket_id, from_status, to_status, actor, timestamp, note)
           VALUES (?, 'in_progress', 'blocked', 'sift', ?, ?)""",
        (ticket_id, ts, note),
    )
    conn.commit()


def run_loop(db_path: str, reports_dir: str) -> None:
    log.info("Sift research executor starting — db=%s reports=%s", db_path, reports_dir)

    reports = Path(reports_dir)
    reports.mkdir(parents=True, exist_ok=True)

    conn = connect_db(db_path)

    # Load Brave API key once at startup
    brave_key = load_brave_key()
    if brave_key:
        log.info("Brave Search API key loaded — web search enabled")
    else:
        log.warning("No Brave API key found at %s — Sift will use LLM knowledge only", BRAVE_KEY_PATH)

    while not _shutdown:
        # Detect model each cycle (in case it changes)
        model = detect_model()
        if not model:
            log.warning("Lemonade not available or no model loaded — sleeping %ds", SLEEP_SECONDS)
            time.sleep(SLEEP_SECONDS)
            continue

        ticket = fetch_next_ticket(conn)
        if not ticket:
            log.debug("No queued tickets — sleeping %ds", SLEEP_SECONDS)
            time.sleep(SLEEP_SECONDS)
            continue

        ticket_id = ticket["ticket_id"]
        question = ticket["ticket_description"] or ""
        log.info("Processing ticket %s: %s", ticket_id, question[:80])

        mark_in_progress(conn, ticket_id)

        try:
            # Web search phase
            search_context = ""
            if brave_key:
                log.info("Searching web for: %s", question[:60])
                results = brave_search(question, brave_key)
                if results:
                    log.info("Got %d search results", len(results))
                    search_context = format_search_context(results)
                else:
                    log.info("No search results — proceeding with LLM knowledge only")

            # LLM generation phase
            report_text = call_lemonade(model, question, search_context)
            report_path = reports / f"{ticket_id}.report.md"
            report_path.write_text(report_text, encoding="utf-8")
            log.info("Report written to %s (%d chars)", report_path, len(report_text))
            mark_complete(conn, ticket_id, str(report_path.resolve()))
        except Exception as exc:
            log.error("Failed to process ticket %s: %s", ticket_id, exc)
            mark_failed(conn, ticket_id, str(exc))

    conn.close()
    log.info("Sift executor shut down cleanly.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Sift research executor")
    parser.add_argument("--db-path", required=True, help="Path to research SQLite DB")
    parser.add_argument("--reports-dir", required=True, help="Directory to write reports into")
    args = parser.parse_args()

    run_loop(args.db_path, args.reports_dir)


if __name__ == "__main__":
    main()
