import sqlite3
import json
import asyncio
import os
import logging
from typing import AsyncGenerator

log = logging.getLogger(__name__)


class DbWatcher:
    def __init__(self, db_path: str, poll_interval: float = 1.0):
        self.db_path = db_path
        self.poll_interval = poll_interval
        self._last_state: dict[str, dict] = {}

    def _read_tickets(self) -> list[dict]:
        if not os.path.exists(self.db_path):
            return []
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                "SELECT id, status, gate, assignee, parent_ticket_id, updated_at, failure_count, blocked_reason_code FROM tickets ORDER BY id"
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            log.warning("DB read error: %s", e)
            return []
        finally:
            conn.close()

    def get_all_tickets(self) -> list[dict]:
        return self._read_tickets()

    async def watch(self) -> AsyncGenerator[dict, None]:
        tickets = self._read_tickets()
        state = {t["id"]: t for t in tickets}
        self._last_state = state
        yield {"type": "snapshot", "tickets": tickets}
        while True:
            await asyncio.sleep(self.poll_interval)
            tickets = self._read_tickets()
            new_state = {t["id"]: t for t in tickets}
            changes = []
            for tid, tdata in new_state.items():
                old = self._last_state.get(tid)
                if old is None or old != tdata:
                    changes.append(tdata)
            if changes:
                self._last_state = new_state
                yield {"type": "update", "tickets": changes}
