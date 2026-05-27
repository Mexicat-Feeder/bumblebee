"""
init_research.py — CLI to create and optionally seed a standalone research DB.

Usage:
    python scripts/init_research.py --db-path ./research/research.db --reports-dir ./research/reports
    python scripts/init_research.py --db-path ./research/research.db --reports-dir ./research/reports --seed-demo
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow running from the repo root: import engine modules
_repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_repo_root))

from engine.research_db import init_research_db  # noqa: E402


DEMO_REPORTS = {
    "RSH-001": {
        "question": "Best practices for food cart ordering UX on mobile devices",
        "description": "Research best practices and patterns for mobile ordering UX at food carts and small vendors. Focus on speed, simplicity, and reducing friction for customers who are standing in line.",
    },
    "RSH-002": {
        "question": "Payment processing options for small food vendors",
        "description": "Evaluate payment processing options suitable for small food cart vendors. Compare fees, hardware requirements, offline capability, and ease of setup.",
    },
}

RSH_001_REPORT = """\
# Food Cart Mobile Ordering UX — Best Practices

## Executive Summary

Mobile ordering at food carts succeeds when it removes friction, not adds it. The best implementations let customers order in under 60 seconds with no account required. Speed and simplicity win; fancy features lose.

## Key Findings

### 1. Reduce Tap Count to Order

Every extra tap costs a conversion. The top-performing food cart ordering apps keep the path to checkout at 3–4 taps: browse → customize → pay. Features that require more taps (account creation, loyalty sign-up, upsell screens) should be optional or post-order only.

**Patterns that work:**
- Single-page scrolling menu (no sub-navigation)
- Quantity stepper inline with the item (no separate "add to cart" modal)
- Sticky "View Order / Checkout" button visible at all times
- Apple Pay / Google Pay as the default payment — eliminates card entry entirely

### 2. Optimize for Outdoor Legibility

Food carts operate in sunlight. Text and buttons must be readable in direct sun:
- Minimum body font: 16px, headers 20px+
- High-contrast color scheme (avoid low-contrast grey-on-white)
- Touch targets minimum 48×48px (Apple HIG recommendation)
- Avoid relying on color alone to communicate state (e.g., use icons + color for "sold out")

### 3. Queue Visibility Reduces Abandonment

Customers standing in line want to know their order will be ready when they reach the window. Show:
- Estimated wait time (even a rough "5–10 min" helps)
- Order number prominently after checkout
- Optional SMS notification for "order ready" (Twilio Basic ~$0.01/msg)

### 4. No Account Required (Guest Checkout First)

Requiring account creation before ordering is the single biggest drop-off point. Offer:
1. Guest checkout (email/phone optional)
2. "Save my info" prompt *after* successful order
3. Account creation only if customer wants order history

### 5. Offline Resilience

Food cart venues often have poor cell coverage. Design for graceful degradation:
- Cache menu locally on first load (service worker or localStorage)
- Queue orders locally if network drops; retry on reconnect
- Show "limited connectivity" warning rather than blank error screen

## Practical Recommendations

| Priority | Action | Effort |
|----------|--------|--------|
| High | Implement Apple Pay / Google Pay | 1–2 days |
| High | Remove required account creation | < 1 day |
| Medium | Add estimated wait time display | 1 day |
| Medium | Cache menu for offline use | 1–2 days |
| Low | SMS order-ready notification | 1 day |

## References & Sources

- Apple Human Interface Guidelines — Touch Target Size: https://developer.apple.com/design/human-interface-guidelines/buttons
- Google Material Design — Mobile UX patterns: https://m3.material.io/foundations/accessible-design/overview
- Baymard Institute Mobile UX research (2023): Guest checkout reduces abandonment by 23%
- Square Developer Docs (in-app payments SDK): https://developer.squareup.com/docs/in-app-payments-sdk
"""

RSH_002_REPORT = """\
# Payment Processing Options for Small Food Vendors

## Executive Summary

For small food carts, Square and Stripe Terminal are the dominant choices with sub-3% fees and solid offline capability. The right choice depends on whether you need in-person hardware, mobile-only, or integrated online+in-person. Avoid legacy processors with monthly minimums — they're designed for higher-volume retail, not carts.

## Key Findings

### 1. Fee Comparison (2024 rates)

| Processor | Card Present Rate | Online Rate | Monthly Fee | Offline? |
|-----------|-------------------|-------------|-------------|---------|
| Square | 2.6% + $0.10 | 2.9% + $0.30 | $0 | ✅ (queue + retry) |
| Stripe Terminal | 2.7% + $0.05 | 2.9% + $0.30 | $0 | ✅ (offline mode) |
| PayPal Zettle | 2.29% + $0.09 | 3.49% + $0.49 | $0 | ✅ |
| Clover Go | 2.6% + $0.10 | 3.5% + $0.10 | $0–$14.95 | ⚠️ Limited |
| Toast (card present) | 2.49% + $0.15 | N/A | $110+/mo | ✅ | 

**Takeaway:** Square and Stripe Terminal are nearly identical on price. PayPal Zettle is slightly cheaper for high-volume card-present. Toast only makes sense at restaurant scale.

### 2. Hardware Options

**Square Reader** ($49 one-time or free first reader)
- Plugs into headphone jack or Lightning/USB-C
- Square Terminal ($299): standalone screen + printer
- Battery life: Reader needs phone; Terminal is 8+ hrs standalone

**Stripe Terminal**
- BBPOS WisePOS E: $249, runs Android, integrates with Stripe SDK
- Stripe Reader M2: $59, Bluetooth, pairs with mobile app
- Best for custom-built ordering apps (Stripe's SDK is developer-friendly)

**PayPal Zettle**
- Card reader $29, good for basic tap/chip/swipe
- No monthly fees, funds in 1–2 business days

### 3. Offline Capability

All three top choices queue transactions locally when connectivity drops:
- **Square**: Stores up to 200 offline transactions, auto-syncs when back online. Limit: $50K per offline period.
- **Stripe Terminal**: Offline mode must be explicitly enabled; stores encrypted transactions locally for up to 30 days.
- **PayPal Zettle**: Offline payments capped at $2,000/day; auto-syncs.

### 4. Integration with Ordering Apps

If building a custom ordering app:
- **Stripe Terminal** is the strongest choice — the JavaScript/iOS/Android SDKs are mature, well-documented, and actively maintained.
- **Square** has a solid In-App Payments SDK but the docs lag slightly behind Stripe's.
- **PayPal Zettle** has limited SDK support for custom integrations.

### 5. Payout Speed

| Processor | Standard Payout | Instant Payout |
|-----------|-----------------|----------------|
| Square | Next business day | Instant (1.75% fee) |
| Stripe | 2 business days | Instant (1.5% fee, min $0.50) |
| PayPal Zettle | 1–2 business days | PayPal balance (instant, free) |

## Practical Recommendations

1. **For a mobile-only setup with no custom app**: Square Reader (free first reader, no monthly fees, excellent offline mode).
2. **For a custom-built ordering app**: Stripe Terminal + BBPOS reader. Better SDK, more flexible, slightly lower card-present rate.
3. **For the highest volume / standalone terminal**: PayPal Zettle Reader (lowest flat rate at high volume).
4. **Avoid**: Any processor with monthly minimums unless processing >$10K/month.

## Key Contacts / Setup Links

- Square: https://squareup.com/us/en/point-of-sale/food-truck
- Stripe Terminal: https://stripe.com/terminal
- PayPal Zettle: https://www.zettle.com/us
- Stripe Terminal SDK docs: https://stripe.com/docs/terminal/sdk
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def seed_demo(conn: sqlite3.Connection, reports_dir: Path) -> None:
    """Insert 2 pre-completed research tickets with full reports."""
    reports_dir.mkdir(parents=True, exist_ok=True)
    ts = now_iso()

    report_content = {"RSH-001": RSH_001_REPORT, "RSH-002": RSH_002_REPORT}

    for ticket_id, meta in DEMO_REPORTS.items():
        report_path = (reports_dir / f"{ticket_id}.report.md").resolve()
        report_path.write_text(report_content[ticket_id], encoding="utf-8")

        # tickets
        conn.execute(
            """
            INSERT OR IGNORE INTO tickets (id, owner, gate, status, depends_on, updated_at)
            VALUES (?, 'research', 1, 'qa_verified', '[]', ?)
            """,
            (ticket_id, ts),
        )
        # ticket_requirements
        conn.execute(
            """
            INSERT OR IGNORE INTO ticket_requirements
                (ticket_id, ticket_description, worker_done_criteria, qa_done_criteria, updated_at)
            VALUES (?, ?, 'Report delivered', 'Human reviewed', ?)
            """,
            (ticket_id, meta["description"], ts),
        )
        # research_queue
        conn.execute(
            """
            INSERT OR IGNORE INTO research_queue
                (ticket_id, requested_by, consumed_by, closure_mode, queue_status,
                 priority, brief_path, report_path, review_path,
                 enqueued_at, last_attempt_at, last_note, attempt_count)
            VALUES (?, 'dashboard', 'sift', 'auto', 'human_acked',
                    5, '', ?, '',
                    ?, ?, 'Demo seed data', 1)
            """,
            (ticket_id, str(report_path), ts, ts),
        )
        # ticket_events
        conn.execute(
            """
            INSERT INTO ticket_events (ticket_id, from_status, to_status, actor, timestamp, note)
            VALUES (?, NULL, 'queued', 'system', ?, 'Demo seed: created')
            """,
            (ticket_id, ts),
        )
        conn.execute(
            """
            INSERT INTO ticket_events (ticket_id, from_status, to_status, actor, timestamp, note)
            VALUES (?, 'queued', 'qa_verified', 'sift', ?, 'Demo seed: report delivered')
            """,
            (ticket_id, ts),
        )
        print(f"  Seeded {ticket_id}: {meta['question']}")
        print(f"    Report -> {report_path}")

    conn.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize a standalone research SQLite DB")
    parser.add_argument("--db-path", required=True, help="Path to create the research DB")
    parser.add_argument("--reports-dir", required=True, help="Directory to write reports into")
    parser.add_argument(
        "--seed-demo",
        action="store_true",
        help="Seed with demo food-cart research tickets",
    )
    args = parser.parse_args()

    db_path = Path(args.db_path)
    reports_dir = Path(args.reports_dir)

    db_path.parent.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")

    print(f"Initializing research DB at {db_path.resolve()}")
    init_research_db(conn)
    print("  Tables created: tickets, ticket_requirements, ticket_events, research_queue")

    if args.seed_demo:
        print("Seeding demo data...")
        seed_demo(conn, reports_dir)

    conn.close()
    print(f"Done. DB: {db_path.resolve()}")


if __name__ == "__main__":
    main()
