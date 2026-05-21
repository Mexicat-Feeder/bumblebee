"""Tests for the Bumblebee declarative state machine."""
import pytest
import sys
from pathlib import Path

# Add engine to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from engine.state_machine import (
    STATES, TERMINAL_STATES, TRANSITIONS, BLOCKED_REASON_CODES,
    BLOCKED_CODE_ROUTING, RETRY_LIMITS, ASSIGNEES,
    StateMachine, Transition, TicketState,
    InvalidTransition, NoValidTransition,
)


# ── Fixtures ──────────────────────────────────────────────────────

def _noop_guard(ticket, context):
    return True

def _false_guard(ticket, context):
    return False

def _noop_effect(ticket, transition, context):
    pass

def make_sm(**kwargs) -> StateMachine:
    """Create a state machine with all guards/effects registered as noops."""
    sm = StateMachine(**kwargs)
    for name in sm.all_guard_names():
        sm.register_guard(name, _noop_guard)
    for name in sm.all_side_effect_names():
        sm.register_side_effect(name, _noop_effect)
    return sm


# ── Schema validation tests ───────────────────────────────────────

class TestSchemaValidation:

    def test_default_schema_is_valid(self):
        """The default state machine definition must pass validation."""
        sm = make_sm()
        assert sm is not None

    def test_all_states_have_at_least_one_outbound_transition(self):
        """Every non-terminal state must have at least one way out."""
        sm = make_sm()
        for state in STATES - TERMINAL_STATES:
            transitions = sm.valid_transitions(state)
            assert len(transitions) > 0, (
                f"State '{state}' has no outbound transitions"
            )

    def test_no_unreachable_states(self):
        """Every state (except todo) must be reachable via some transition."""
        reachable = {"todo"}
        for t in TRANSITIONS:
            reachable.add(t.to_state)
        unreachable = STATES - reachable
        assert unreachable == set(), f"Unreachable states: {unreachable}"

    def test_terminal_states_have_no_outbound(self):
        """Terminal states should not have outbound transitions."""
        sm = make_sm()
        for state in TERMINAL_STATES:
            transitions = sm.valid_transitions(state)
            assert len(transitions) == 0, (
                f"Terminal state '{state}' has outbound transitions: {[t.name for t in transitions]}"
            )

    def test_blocked_reason_codes_all_have_routing(self):
        """Every blocked_reason_code must map to a routing strategy.
        This is the test that would have caught Run #2 Issues #10, #25."""
        for code in BLOCKED_REASON_CODES:
            assert code in BLOCKED_CODE_ROUTING, (
                f"Blocked code '{code}' has no routing rule"
            )

    def test_blocked_routing_only_references_known_codes(self):
        """No phantom routing rules for codes that don't exist."""
        for code in BLOCKED_CODE_ROUTING:
            assert code in BLOCKED_REASON_CODES, (
                f"Routing rule for '{code}' but code not in BLOCKED_REASON_CODES"
            )

    def test_transition_guards_are_named(self):
        """Every transition has a non-empty guard name."""
        for t in TRANSITIONS:
            assert t.guard, f"Transition '{t.name}' has empty guard"

    def test_transition_names_are_unique(self):
        """No two transitions share the same name."""
        names = [t.name for t in TRANSITIONS]
        assert len(names) == len(set(names)), (
            f"Duplicate transition names: {[n for n in names if names.count(n) > 1]}"
        )

    def test_schema_rejects_missing_outbound(self):
        """A state with no outbound transitions (and not terminal) must fail validation."""
        with pytest.raises(ValueError, match="no outbound transitions"):
            StateMachine(
                states={"todo", "orphan", "done"},
                terminal_states={"done"},
                transitions=(
                    Transition("todo", "orphan", "go_orphan", "always_true", "executor"),
                    # orphan has no way out and is not terminal
                ),
                blocked_codes=set(),
                blocked_routing={},
            )

    def test_schema_rejects_unrouted_blocked_code(self):
        """A blocked code with no routing rule must fail validation."""
        with pytest.raises(ValueError, match="no routing rule"):
            StateMachine(
                states={"todo", "blocked"},
                terminal_states=set(),
                transitions=(
                    Transition("todo", "blocked", "block_it", "always", "x"),
                    Transition("blocked", "todo", "unblock", "always", "x"),
                ),
                blocked_codes={"mystery_code"},
                blocked_routing={},  # missing!
            )


# ── Transition logic tests ────────────────────────────────────────

class TestTransitions:

    def test_valid_transition_succeeds(self):
        sm = make_sm()
        ticket = TicketState(ticket_id="T-1", status="todo")
        t = sm.transition(ticket, "in_progress")
        assert ticket.status == "in_progress"
        assert t.name == "claim_ticket"

    def test_invalid_transition_raises(self):
        """Cannot jump from todo directly to qa_verified."""
        sm = make_sm()
        ticket = TicketState(ticket_id="T-1", status="todo")
        with pytest.raises(InvalidTransition):
            sm.transition(ticket, "qa_verified")

    def test_guard_failure_raises(self):
        """Transition exists but guard rejects it."""
        sm = make_sm()
        sm.register_guard("deps_satisfied_and_requirements_exist", _false_guard)
        ticket = TicketState(ticket_id="T-1", status="todo")
        with pytest.raises(InvalidTransition, match="Guard.*failed"):
            sm.transition(ticket, "in_progress")

    def test_side_effects_execute(self):
        sm = make_sm()
        calls = []
        sm.register_side_effect("log_event", lambda t, tr, c: calls.append("log"))
        ticket = TicketState(ticket_id="T-1", status="todo")
        sm.transition(ticket, "in_progress")
        assert "log" in calls

    def test_assignee_set_on_transition(self):
        sm = make_sm()
        ticket = TicketState(ticket_id="T-1", status="todo")
        sm.transition(ticket, "in_progress")
        assert ticket.assignee == "executor"

    def test_assignee_cleared_on_return_to_todo(self):
        sm = make_sm()
        ticket = TicketState(ticket_id="T-1", status="blocked", assignee="coding-agent")
        sm.transition(ticket, "todo", name="retry_ticket")
        assert ticket.assignee is None

    def test_blocked_code_set_on_transition(self):
        sm = make_sm()
        ticket = TicketState(ticket_id="T-1", status="in_progress")
        sm.transition(ticket, "blocked", name="parent_waiting_on_children")
        assert ticket.blocked_reason_code == "waiting_on_child_packets"

    def test_full_happy_path(self):
        """Walk a ticket from todo → qa_verified."""
        sm = make_sm()
        ticket = TicketState(ticket_id="T-1", status="todo")

        sm.transition(ticket, "in_progress")
        assert ticket.status == "in_progress"

        sm.transition(ticket, "done", name="worker_check_passed")
        assert ticket.status == "done"

        sm.transition(ticket, "qa_verified")
        assert ticket.status == "qa_verified"

    def test_blocked_retry_cycle(self):
        """blocked → todo → in_progress → done cycle."""
        sm = make_sm()
        ticket = TicketState(ticket_id="T-1", status="blocked", blocked_reason_code="timeout")

        sm.transition(ticket, "todo", name="retry_ticket")
        assert ticket.status == "todo"

        sm.transition(ticket, "in_progress")
        assert ticket.status == "in_progress"

        sm.transition(ticket, "done", name="worker_check_passed")
        assert ticket.status == "done"

    def test_qa_failure_cycle(self):
        """done → blocked (qa failed) → todo (retry)."""
        sm = make_sm()
        ticket = TicketState(ticket_id="T-1", status="done")

        sm.transition(ticket, "blocked", name="qa_failed")
        assert ticket.status == "blocked"

        sm.transition(ticket, "todo", name="retry_ticket")
        assert ticket.status == "todo"

    def test_human_review_cycle(self):
        """blocked → human_review → todo."""
        sm = make_sm()
        ticket = TicketState(ticket_id="T-1", status="blocked")

        sm.transition(ticket, "human_review", name="escalate_to_human")
        assert ticket.status == "human_review"
        assert ticket.assignee == "human-review"

        sm.transition(ticket, "todo", name="human_approved")
        assert ticket.status == "todo"
        assert ticket.assignee is None

    def test_parent_waiting_then_children_complete(self):
        """in_progress → blocked (waiting) → todo (children done)."""
        sm = make_sm()
        ticket = TicketState(ticket_id="T-1", status="in_progress")

        sm.transition(ticket, "blocked", name="parent_waiting_on_children")
        assert ticket.blocked_reason_code == "waiting_on_child_packets"

        sm.transition(ticket, "todo", name="children_complete")
        assert ticket.status == "todo"

    def test_manual_fix_path(self):
        """blocked → done (Pixel manual fix)."""
        sm = make_sm()
        ticket = TicketState(ticket_id="T-1", status="blocked")

        sm.transition(ticket, "done", name="manual_fix_applied")
        assert ticket.status == "done"


# ── Blocked code routing tests ────────────────────────────────────

class TestBlockedRouting:

    def test_all_transient_codes_route_to_retry(self):
        sm = make_sm()
        transient = {"timeout", "stall_timeout"}
        for code in transient:
            assert sm.route_blocked(code) == "retry"

    def test_coding_bound_codes_route_to_coding(self):
        sm = make_sm()
        coding = {"implementation_missing", "qa_failure", "human_rejected", "preview_evidence_missing"}
        for code in coding:
            assert sm.route_blocked(code) == "coding"

    def test_structural_codes_route_to_pixel_review(self):
        sm = make_sm()
        structural = {"requirements_missing", "requirements_invalid", "pixel_review_required"}
        for code in structural:
            assert sm.route_blocked(code) == "pixel_review"

    def test_unknown_code_raises(self):
        sm = make_sm()
        with pytest.raises(ValueError, match="Unknown blocked_reason_code"):
            sm.route_blocked("totally_fake_code")

    def test_waiting_on_children_routes_to_hold(self):
        sm = make_sm()
        assert sm.route_blocked("waiting_on_child_packets") == "hold"


# ── Run #2 issue replay tests ─────────────────────────────────────

class TestRun2IssueReplay:
    """Replay each state-machine-gap issue from Run #2.
    Each must either succeed (valid transition) or raise (caught error).
    None may silently ignore."""

    def test_issue10_stall_timeout_has_routing(self):
        """Issue #10: stall_timeout not routed by orchestrator.
        In the old system, stall_timeout tickets were silently ignored."""
        sm = make_sm()
        route = sm.route_blocked("stall_timeout")
        assert route == "retry"  # not silently ignored

    def test_issue12_no_separate_coding_queue_table(self):
        """Issue #12: coding_queue / tickets sync failures.
        In Bumblebee, there's no separate coding_queue table.
        Coding dispatch is managed within the single-cycle executor."""
        # The state machine handles coding-bound tickets via blocked → todo
        sm = make_sm()
        ticket = TicketState(ticket_id="T-1", status="blocked",
                           blocked_reason_code="implementation_missing")
        route = sm.route_blocked("implementation_missing")
        assert route == "coding"
        # And the ticket can transition back to todo
        assert sm.can_transition("blocked", "todo")

    def test_issue25_missing_requirements_no_phantom_bugs(self):
        """Issue #25: parent missing ticket_requirements → phantom bug cascade.
        The state machine must route requirements_missing to pixel_review,
        not create a bug ticket."""
        sm = make_sm()
        route = sm.route_blocked("requirements_missing")
        assert route == "pixel_review"  # escalate, don't create phantom bugs

    def test_issue11_manual_fix_state_is_done(self):
        """Issue #11: correct state after Pixel manual fix was unclear.
        The state machine has an explicit manual_fix_applied transition → done."""
        sm = make_sm()
        ticket = TicketState(ticket_id="T-1", status="blocked")
        sm.transition(ticket, "done", name="manual_fix_applied")
        assert ticket.status == "done"
        # From done, QA picks it up
        assert sm.can_transition("done", "qa_verified")

    def test_issue3_timeout_is_retriable(self):
        """Issue #3: Forge hangs → timeout. Must be retryable."""
        sm = make_sm()
        assert sm.route_blocked("timeout") == "retry"
        assert sm.can_transition("blocked", "todo")

    def test_no_silent_ignore_for_any_blocked_code(self):
        """No blocked code should result in a ticket being silently ignored.
        Every code routes somewhere."""
        sm = make_sm()
        for code in BLOCKED_REASON_CODES:
            route = sm.route_blocked(code)
            assert route is not None and route != "", (
                f"Blocked code '{code}' has no routing"
            )


# ── Guard/effect registration tests ──────────────────────────────

class TestRegistration:

    def test_unregistered_guard_raises(self):
        sm = StateMachine()  # no guards registered
        ticket = TicketState(ticket_id="T-1", status="todo")
        with pytest.raises(ValueError, match="Guard.*not registered"):
            sm.transition(ticket, "in_progress")

    def test_unregistered_side_effect_raises(self):
        sm = StateMachine()
        for name in sm.all_guard_names():
            sm.register_guard(name, _noop_guard)
        # Don't register side effects
        ticket = TicketState(ticket_id="T-1", status="todo")
        with pytest.raises(ValueError, match="Side effect.*not registered"):
            sm.transition(ticket, "in_progress")

    def test_all_guards_registered_check(self):
        sm = make_sm()
        assert sm.guards_registered()

    def test_all_side_effects_registered_check(self):
        sm = make_sm()
        assert sm.side_effects_registered()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
