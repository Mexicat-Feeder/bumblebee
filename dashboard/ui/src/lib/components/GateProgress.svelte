<script lang="ts">
  import { ticketStore } from '$lib/stores/tickets';
  import type { Ticket } from '$lib/stores/tickets';

  export let onSelectGate: (gate: number) => void = () => {};
  export let selectedGate: number | null = null;

  const GATE_NAMES: Record<number, string> = {
    0: 'Backend Services',
    1: 'Skeleton',
    2: 'Feature Components',
    3: 'Error Boundaries',
    4: 'Visual Polish',
  };

  const GATE_DESC: Record<number, string> = {
    0: 'APIs, data layer, and service foundations',
    1: 'App shell, stores, navigation, and routing',
    2: 'Vertical slices — each feature end-to-end',
    3: 'Graceful failure states and resilience',
    4: 'Layout refinement and final polish',
  };

  // All ticket gates are Forge-driven
  const TICKET_ACTOR = '🤖';

  interface GateInfo {
    gate: number; name: string; desc: string;
    total: number; done: number;
    status: 'complete'|'active'|'pending';
    actor: string;
    isTicketGate: boolean;
  }

  // Non-ticket gate status — will come from registry/API eventually
  // For now, hardcoded based on project state
  export let manualGates: Record<number, 'complete'|'active'|'pending'> = {};

  function deriveGates(tickets: Ticket[]): GateInfo[] {
    // Ticket-driven gates (0-3)
    const byGate = new Map<number, Ticket[]>();
    for (const t of tickets) {
      const arr = byGate.get(t.gate) || [];
      arr.push(t);
      byGate.set(t.gate, arr);
    }
    const ticketGates = Array.from(byGate.keys()).sort((a,b) => a-b).map(g => {
      const tix = byGate.get(g)!;
      const done = tix.filter(t => t.status === 'qa_verified').length;
      let status: GateInfo['status'] = 'pending';
      if (done === tix.length) status = 'complete';
      else if (tix.some(t => t.status === 'in_progress' || t.status === 'done')) status = 'active';
      return {
        gate: g, name: GATE_NAMES[g] ?? `Phase ${g}`, desc: GATE_DESC[g] ?? '',
        total: tix.length, done, status,
        actor: TICKET_ACTOR,
        isTicketGate: true,
      };
    });

    // Non-ticket gates: checklist-driven, numbered after the last ticket gate
    const maxTicketGate = ticketGates.length > 0 ? Math.max(...ticketGates.map(g => g.gate)) : -1;
    const allTicketsDone = ticketGates.length > 0 && ticketGates.every(g => g.status === 'complete');
    const PROCESS_STEPS = [
      { key: 'integration', name: 'Integration', desc: 'Shared file wiring \u2014 Pixel', actor: '\ud83d\udc3e' },
      { key: 'smoke',       name: 'Smoke Test',  desc: 'App renders, no errors \u2014 Pixel', actor: '\ud83d\udc3e' },
      { key: 'review',      name: 'Visual Review', desc: 'Human sign-off', actor: '\ud83d\udc64' },
    ];
    const processGates: GateInfo[] = PROCESS_STEPS.map((step, i) => {
      const g = maxTicketGate + 1 + i;
      let status: GateInfo['status'] = 'pending';
      // Check manualGates by gate number first
      if (manualGates[g]) {
        status = manualGates[g];
      } else if (allTicketsDone) {
        // If all Forge gates are done and no manual override, assume complete
        status = 'complete';
      }
      return {
        gate: g, name: step.name, desc: step.desc,
        total: 1, done: status === 'complete' ? 1 : 0, status,
        actor: step.actor,
        isTicketGate: false,
      };
    });

    return [...ticketGates, ...processGates];
  }

  $: _tickets = $ticketStore.tickets;
  $: gates = deriveGates(_tickets);
  $: if (selectedGate === null && gates.length > 0) {
    const active = gates.find(g => g.status === 'active') || gates[0];
    selectedGate = active.gate;
    onSelectGate(active.gate);
  }
</script>

<div class="gate-row">
  {#each gates as gate (gate.gate)}
    {#if gate !== gates[0]}
      <span class="gate-arrow">→</span>
    {/if}
    <button
      class="gate-card {gate.status}"
      class:selected={selectedGate === gate.gate}
      on:click={() => { selectedGate = gate.gate; onSelectGate(gate.gate); }}
      type="button"
    >
      <div class="gate-header">
        <span class="gate-num">{gate.actor} GATE {gate.gate}</span>
        <span class="gate-name">{gate.name}</span>
        <span class="gate-desc">{gate.desc}</span>
      </div>
      <div class="gate-footer">
        {#if gate.isTicketGate}
          <span class="gate-count">{gate.done}/{gate.total}</span>
          <div class="gate-bar">
            <div
              class="gate-bar-fill gate-fill-{gate.status}"
              style="width: {gate.total > 0 ? (gate.done / gate.total) * 100 : 0}%"
            ></div>
          </div>
        {:else}
          <span class="gate-count">{gate.status === 'complete' ? '✓ Done' : gate.status === 'active' ? '◌ In progress' : '—'}</span>
        {/if}
      </div>
    </button>
  {/each}
</div>

<style>
  .gate-row {
    display: flex;
    align-items: stretch;
    gap: 8px;
    width: 100%;
    height: 100%;
  }

  .gate-arrow {
    color: var(--color-text-muted);
    font-size: 1.2rem;
    display: flex;
    align-items: center;
    flex-shrink: 0;
  }

  .gate-card {
    background: var(--color-bg-panel);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: var(--radius-panel);
    padding: 14px 16px;
    min-height: 120px;
    flex: 1;
    cursor: pointer;
    transition: background 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    text-align: left;
    font-family: inherit;
    color: inherit;
    box-shadow: 0 4px 32px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.04);
  }

  .gate-card:hover {
    background: var(--color-bg-panel-raised);
  }

  .gate-header {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .gate-num {
    font-size: 0.65rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--color-text-muted);
  }

  .gate-name {
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--color-text-primary);
  }

  .gate-desc {
    font-size: 0.72rem;
    color: var(--color-text-muted);
    line-height: 1.4;
    margin-top: 2px;
  }

  .gate-footer {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .gate-count {
    font-size: var(--text-body);
    font-family: var(--font-mono);
    color: var(--color-text-secondary);
  }

  .gate-bar {
    height: 6px;
    border-radius: 3px;
    background: var(--color-bg-base);
    overflow: hidden;
  }

  .gate-bar-fill {
    height: 100%;
    border-radius: 3px;
    transition: width 400ms ease-out;
  }

  /* Status variants */
  .gate-card.complete {
    border-left: 3px solid var(--color-accent-complete);
    box-shadow: 0 0 20px rgba(45, 230, 230, 0.25), 0 4px 32px rgba(0,0,0,0.5);
  }
  .gate-card.active {
    border-left: 3px solid var(--color-accent-primary);
    box-shadow: 0 0 20px rgba(58, 190, 255, 0.25), 0 4px 32px rgba(0,0,0,0.5);
  }
  .gate-card.pending {
    border-left: 3px solid var(--color-text-muted);
    box-shadow: 0 4px 32px rgba(0,0,0,0.5);
  }
  .gate-card.selected {
    background: var(--color-bg-panel-raised);
    border-color: rgba(255,255,255,0.15);
  }

  .gate-fill-complete { background: var(--color-accent-complete); }
  .gate-fill-active   { background: var(--color-accent-primary); }
  .gate-fill-pending  { background: var(--color-text-muted); }
</style>
