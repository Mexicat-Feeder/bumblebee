"""
Swarm Engine — Declarative State Machine

Every ticket state, every valid transition, every guard, every side effect —
declared in one place. The executor calls transition() and the state machine
enforces the rules.

If a ticket is in a state with no valid transition for its conditions,
that's a schema error — raised immediately, never silently ignored.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

# ---------------------------------------------------------------------------
# States
# ---------------------------------------------------------------------------

STATES: set[str] = {
    "todo",
    "in_progress",
    "blocked",
    "done",
    "qa_verified",
    "human_review",
}

# Terminal states — no outbound transitions expected
TERMINAL_STATES: set[str] = {"qa_verified"}

# ---------------------------------------------------------------------------
# Blocked reason codes — every code must have a routing rule
# ---------------------------------------------------------------------------

BLOCKED_REASON_CODES: set[str] = {
    # Transient (auto-retry after cooldown)
    "timeout",
    "stall_timeout",
    "execution_failure",

    # Coding-bound (route to Forge dispatch)
    "implementation_missing",
    "qa_failure",
    "human_rejected",
    "preview_evidence_missing",

    # Structural (route to pixel-review)
    "requirements_missing",
    "requirements_invalid",
    "requirements_unmet",
    "checks_not_implemented",
    "research_required",
    "pixel_review_required",

    # Human gate
    "human_required",

    # Security
    "security_policy",

    # Parent waiting
    "waiting_on_child_packets",
}

# How each blocked code is handled
BLOCKED_CODE_ROUTING: dict[str, str] = {
    # Transient → auto-retry
    "timeout": "retry",
    "stall_timeout": "retry",
    "execution_failure": "retry_then_coding",

    # Coding-bound → dispatch to Forge
    "implementation_missing": "coding",
    "qa_failure": "coding",
    "human_rejected": "coding",
    "preview_evidence_missing": "coding",

    # Structural → pixel-review
    "requirements_missing": "pixel_review",
    "requirements_invalid": "pixel_review",
    "requirements_unmet": "pixel_review",
    "checks_not_implemented": "pixel_review",
    "research_required": "pixel_review",
    "pixel_review_required": "pixel_review",

    # Human gate → human_review
    "human_required": "human_review",

    # Security → pixel_review
    "security_policy": "pixel_review",

    # Parent waiting → hold (re-check each cycle)
    "waiting_on_child_packets": "hold",
}

# Retry limits per routing type
RETRY_LIMITS: dict[str, dict[str, int]] = {
    "retry": {"max_attempts": 3, "cooldown_seconds": 60},
    "stall_timeout": {"max_attempts": 1, "cooldown_seconds": 300},
    "retry_then_coding": {"max_attempts": 2, "cooldown_seconds": 60},
    "coding": {"max_attempts": 3, "cooldown_seconds": 0},
}

# ---------------------------------------------------------------------------
# Assignees
# ---------------------------------------------------------------------------

ASSIGNEES: set[str] = {
    "executor",         # the single-cycle executor owns it
    "coding-agent",     # queued for Forge dispatch
    "pixel-review",     # Pixel diagnoses and fixes
    "human-review",     # human must act
}

# ---------------------------------------------------------------------------
# Transition definition
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Transition:
    """A single valid state transition."""
    from_state: str
    to_state: str
    name: str                          # human-readable identifier
    guard: str                         # name of the guard function
    actor: str                         # who triggers this
    side_effects: tuple[str, ...] = () # side effect function names
    assignee: str | None = None        # set assignee on transition
    blocked_code: str | None = None    # set blocked_reason_code (for → blocked)


TRANSITIONS: tuple[Transition, ...] = (
    # ── todo → in_progress ─────────────────────────────────────────
    Transition(
        from_state="todo",
        to_state="in_progress",
        name="claim_ticket",
        guard="deps_satisfied_and_requirements_exist",
        actor="executor",
        side_effects=("log_event",),
        assignee="executor",
    ),

    # ── in_progress → done (worker check passed) ──────────────────
    Transition(
        from_state="in_progress",
        to_state="done",
        name="worker_check_passed",
        guard="worker_check_passed",
        actor="executor",
        side_effects=("log_event", "capture_screenshot_if_ui"),
    ),

    # ── in_progress → blocked (worker check failed) ───────────────
    Transition(
        from_state="in_progress",
        to_state="blocked",
        name="worker_check_failed",
        guard="worker_check_failed",
        actor="executor",
        side_effects=("log_event", "increment_failure_count"),
    ),

    # ── in_progress → blocked (parent waiting on children) ────────
    Transition(
        from_state="in_progress",
        to_state="blocked",
        name="parent_waiting_on_children",
        guard="has_pending_children",
        actor="executor",
        side_effects=("log_event",),
        blocked_code="waiting_on_child_packets",
    ),

    # ── done → qa_verified (QA passed) ────────────────────────────
    Transition(
        from_state="done",
        to_state="qa_verified",
        name="qa_passed",
        guard="qa_check_passed",
        actor="executor",
        side_effects=("log_event", "check_parent_ready"),
    ),

    # ── done → blocked (QA failed) ────────────────────────────────
    Transition(
        from_state="done",
        to_state="blocked",
        name="qa_failed",
        guard="qa_check_failed",
        actor="executor",
        side_effects=("log_event", "classify_qa_failure"),
    ),

    # ── blocked → todo (retry eligible) ───────────────────────────
    Transition(
        from_state="blocked",
        to_state="todo",
        name="retry_ticket",
        guard="retry_eligible_and_cooldown_elapsed",
        actor="executor",
        side_effects=("log_event", "increment_attempt"),
        assignee=None,  # clear assignee
    ),

    # ── blocked → todo (coding complete, back to orchestrator) ────
    Transition(
        from_state="blocked",
        to_state="todo",
        name="coding_complete",
        guard="coding_queue_done",
        actor="executor",
        side_effects=("log_event",),
        assignee=None,
    ),

    # ── blocked → done (manual fix by Pixel) ──────────────────────
    Transition(
        from_state="blocked",
        to_state="done",
        name="manual_fix_applied",
        guard="manual_fix_verified",
        actor="pixel",
        side_effects=("log_event",),
    ),

    # ── blocked → blocked (re-classify / re-route) ────────────────
    Transition(
        from_state="blocked",
        to_state="blocked",
        name="reclassify_blocked",
        guard="reclassification_needed",
        actor="executor",
        side_effects=("log_event",),
    ),

    # ── blocked → todo (children all done, parent can retry) ──────
    Transition(
        from_state="blocked",
        to_state="todo",
        name="children_complete",
        guard="all_children_qa_verified",
        actor="executor",
        side_effects=("log_event",),
        assignee=None,
    ),

    # ── blocked → human_review ────────────────────────────────────
    Transition(
        from_state="blocked",
        to_state="human_review",
        name="escalate_to_human",
        guard="requires_human_input",
        actor="executor",
        side_effects=("log_event",),
        assignee="human-review",
    ),

    # ── human_review → todo (human approved / provided input) ─────
    Transition(
        from_state="human_review",
        to_state="todo",
        name="human_approved",
        guard="human_input_received",
        actor="human",
        side_effects=("log_event",),
        assignee=None,
    ),

    # ── human_review → blocked (human rejected) ──────────────────
    Transition(
        from_state="human_review",
        to_state="blocked",
        name="human_rejected",
        guard="human_rejected_input",
        actor="human",
        side_effects=("log_event",),
        blocked_code="human_rejected",
    ),
)

# ---------------------------------------------------------------------------
# State machine engine
# ---------------------------------------------------------------------------

class InvalidTransition(Exception):
    """Raised when a requested transition is not valid."""
    pass


class NoValidTransition(Exception):
    """Raised when a ticket has no valid outbound transition."""
    pass


@dataclass
class TicketState:
    """Snapshot of a ticket's current state for transition evaluation."""
    ticket_id: str
    status: str
    blocked_reason_code: str | None = None
    assignee: str | None = None
    failure_count: int = 0
    attempt_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class StateMachine:
    """Declarative state machine for ticket lifecycle."""

    def __init__(
        self,
        states: set[str] = STATES,
        terminal_states: set[str] = TERMINAL_STATES,
        transitions: tuple[Transition, ...] = TRANSITIONS,
        blocked_codes: set[str] = BLOCKED_REASON_CODES,
        blocked_routing: dict[str, str] = BLOCKED_CODE_ROUTING,
        guards: dict[str, Callable] | None = None,
        side_effects: dict[str, Callable] | None = None,
    ):
        self.states = states
        self.terminal_states = terminal_states
        self.transitions = transitions
        self.blocked_codes = blocked_codes
        self.blocked_routing = blocked_routing
        self._guards: dict[str, Callable] = guards or {}
        self._side_effects: dict[str, Callable] = side_effects or {}

        # Build lookup: from_state → list of transitions
        self._from_index: dict[str, list[Transition]] = {}
        for t in transitions:
            self._from_index.setdefault(t.from_state, []).append(t)

        self._validate_schema()

    # ── Schema validation ──────────────────────────────────────────

    def _validate_schema(self) -> None:
        """Validate the state machine definition at construction time."""
        errors: list[str] = []

        # Every non-terminal state must have at least one outbound transition
        for s in self.states - self.terminal_states:
            if s not in self._from_index:
                errors.append(f"State '{s}' has no outbound transitions")

        # Every transition must reference valid states
        for t in self.transitions:
            if t.from_state not in self.states:
                errors.append(f"Transition '{t.name}': from_state '{t.from_state}' not in STATES")
            if t.to_state not in self.states:
                errors.append(f"Transition '{t.name}': to_state '{t.to_state}' not in STATES")

        # Every blocked_reason_code must have a routing rule
        for code in self.blocked_codes:
            if code not in self.blocked_routing:
                errors.append(f"Blocked code '{code}' has no routing rule")

        # Every routing rule must reference a valid strategy
        valid_strategies = {"retry", "retry_then_coding", "coding", "pixel_review", "human_review", "hold"}
        for code, strategy in self.blocked_routing.items():
            if strategy not in valid_strategies:
                errors.append(f"Blocked code '{code}' has invalid strategy '{strategy}'")

        # No unreachable states (every state except 'todo' must be a to_state somewhere)
        reachable = {"todo"}  # start state
        for t in self.transitions:
            reachable.add(t.to_state)
        unreachable = self.states - reachable
        if unreachable:
            errors.append(f"Unreachable states: {unreachable}")

        if errors:
            raise ValueError(
                f"State machine schema errors ({len(errors)}):\n"
                + "\n".join(f"  - {e}" for e in errors)
            )

    # ── Query methods ──────────────────────────────────────────────

    def valid_transitions(self, state: str) -> list[Transition]:
        """Return all transitions available from a given state."""
        return list(self._from_index.get(state, []))

    def outbound_states(self, state: str) -> set[str]:
        """Return all states reachable from a given state."""
        return {t.to_state for t in self.valid_transitions(state)}

    def is_terminal(self, state: str) -> bool:
        return state in self.terminal_states

    def route_blocked(self, blocked_code: str) -> str:
        """Return the routing strategy for a blocked reason code."""
        if blocked_code not in self.blocked_routing:
            raise ValueError(f"Unknown blocked_reason_code: '{blocked_code}'")
        return self.blocked_routing[blocked_code]

    # ── Transition execution ───────────────────────────────────────

    def find_transition(self, from_state: str, to_state: str, name: str | None = None) -> Transition:
        """Find a specific transition. Raises if not found."""
        for t in self._from_index.get(from_state, []):
            if t.to_state == to_state:
                if name is None or t.name == name:
                    return t
        raise InvalidTransition(
            f"No transition from '{from_state}' to '{to_state}'"
            + (f" named '{name}'" if name else "")
        )

    def can_transition(self, from_state: str, to_state: str, name: str | None = None) -> bool:
        """Check if a transition exists (does not evaluate guards)."""
        try:
            self.find_transition(from_state, to_state, name)
            return True
        except InvalidTransition:
            return False

    def evaluate_guard(self, transition: Transition, ticket: TicketState, context: dict[str, Any] | None = None) -> bool:
        """Evaluate a transition's guard function. Returns True if guard passes."""
        guard_fn = self._guards.get(transition.guard)
        if guard_fn is None:
            raise ValueError(f"Guard '{transition.guard}' not registered")
        return guard_fn(ticket, context or {})

    def execute_side_effects(self, transition: Transition, ticket: TicketState, context: dict[str, Any] | None = None) -> None:
        """Execute all side effects for a transition."""
        for effect_name in transition.side_effects:
            effect_fn = self._side_effects.get(effect_name)
            if effect_fn is None:
                raise ValueError(f"Side effect '{effect_name}' not registered")
            effect_fn(ticket, transition, context or {})

    def transition(
        self,
        ticket: TicketState,
        to_state: str,
        name: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> Transition:
        """
        Execute a state transition. 
        
        1. Find the transition
        2. Evaluate the guard
        3. Execute side effects
        4. Update ticket state
        
        Returns the transition that was executed.
        Raises InvalidTransition if the transition doesn't exist.
        Raises InvalidTransition if the guard fails.
        """
        t = self.find_transition(ticket.status, to_state, name)

        if not self.evaluate_guard(t, ticket, context):
            raise InvalidTransition(
                f"Guard '{t.guard}' failed for transition '{t.name}' "
                f"({ticket.status} → {to_state}) on ticket {ticket.ticket_id}"
            )

        self.execute_side_effects(t, ticket, context)

        # Update ticket state
        ticket.status = to_state
        if t.assignee is not None:
            ticket.assignee = t.assignee
        elif to_state == "todo":
            ticket.assignee = None  # clear on return to todo
        if t.blocked_code is not None:
            ticket.blocked_reason_code = t.blocked_code

        return t

    # ── Guard / side effect registration ───────────────────────────

    def register_guard(self, name: str, fn: Callable) -> None:
        self._guards[name] = fn

    def register_side_effect(self, name: str, fn: Callable) -> None:
        self._side_effects[name] = fn

    def all_guard_names(self) -> set[str]:
        return {t.guard for t in self.transitions}

    def all_side_effect_names(self) -> set[str]:
        names: set[str] = set()
        for t in self.transitions:
            names.update(t.side_effects)
        return names

    def guards_registered(self) -> bool:
        return self.all_guard_names() <= set(self._guards.keys())

    def side_effects_registered(self) -> bool:
        return self.all_side_effect_names() <= set(self._side_effects.keys())
