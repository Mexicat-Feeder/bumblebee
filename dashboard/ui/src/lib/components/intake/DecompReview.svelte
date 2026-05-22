<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  export let slug: string;
  export let disabled: boolean = false;

  const dispatch = createEventDispatcher<{
    committed: { ticketsCreated: number };
  }>();

  interface Ticket {
    id: string;
    gate: number;
    description: string;
    required_output_files: string[];
    depends_on: string[];
    is_parent: boolean;
  }

  interface Plan {
    tickets: Ticket[];
    gate_count: number;
    total_tickets: number;
    errors: string[];
  }

  let plan: Plan | null = null;
  let decomposing = false;
  let committing = false;
  let error = '';

  // Group tickets by gate
  $: gateGroups = plan ? groupByGate(plan.tickets) : [];

  function groupByGate(tickets: Ticket[]): { gate: number; tickets: Ticket[] }[] {
    const groups = new Map<number, Ticket[]>();
    for (const t of tickets) {
      const arr = groups.get(t.gate) ?? [];
      arr.push(t);
      groups.set(t.gate, arr);
    }
    return Array.from(groups.entries())
      .sort((a, b) => a[0] - b[0])
      .map(([gate, tickets]) => ({ gate, tickets }));
  }

  async function decompose() {
    decomposing = true;
    error = '';
    plan = null;

    try {
      const resp = await fetch(`/api/projects/${slug}/decompose`, {
        method: 'POST',
      });
      if (!resp.ok) {
        const data = await resp.json().catch(() => ({ detail: resp.statusText }));
        throw new Error(data.detail || `HTTP ${resp.status}`);
      }
      const data = await resp.json();
      plan = data.plan;
      if (plan && plan.errors?.length) {
        error = `Warnings: ${plan.errors.join('; ')}`;
      }
    } catch (e: any) {
      error = e.message || 'Decomposition failed';
    }
    decomposing = false;
  }

  async function commitPlan() {
    if (!plan || committing) return;
    committing = true;
    error = '';

    try {
      const resp = await fetch(`/api/projects/${slug}/decompose/commit`, {
        method: 'POST',
      });
      if (!resp.ok) {
        const data = await resp.json().catch(() => ({ detail: resp.statusText }));
        throw new Error(data.detail || `HTTP ${resp.status}`);
      }
      const data = await resp.json();
      dispatch('committed', { ticketsCreated: data.tickets_created });
    } catch (e: any) {
      error = e.message || 'Failed to commit plan';
    }
    committing = false;
  }
</script>

<section class="decomp-section">
  <div class="decomp-header">
    <h2 class="section-header">TICKET DECOMPOSITION</h2>
    {#if !plan}
      <p class="decomp-hint">Generate a ticket plan from your PRD and Q&A decisions.</p>
    {/if}
  </div>

  <!-- Error -->
  {#if error}
    <div class="decomp-error">
      <span>⚠ {error}</span>
      <button class="dismiss-btn" on:click={() => error = ''}>✕</button>
    </div>
  {/if}

  <!-- No plan yet -->
  {#if !plan && !decomposing}
    <button
      class="btn-decompose"
      on:click={decompose}
      {disabled}
    >
      Decompose PRD into Tickets
    </button>
  {/if}

  <!-- Decomposing spinner -->
  {#if decomposing}
    <div class="decomp-loading">
      <span class="spinner"></span>
      <span>Analyzing PRD and generating tickets...</span>
    </div>
  {/if}

  <!-- Plan review -->
  {#if plan && plan.tickets.length > 0}
    <div class="plan-summary">
      <span class="summary-stat">{plan.total_tickets} tickets</span>
      <span class="summary-dot">·</span>
      <span class="summary-stat">{plan.gate_count} phases</span>
    </div>

    <div class="gate-list">
      {#each gateGroups as group}
        <div class="gate-group">
          <h3 class="gate-header">Phase {group.gate}</h3>
          <div class="ticket-list">
            {#each group.tickets as ticket}
              <div class="ticket-card" class:parent={ticket.is_parent}>
                <div class="ticket-id">{ticket.id}</div>
                <div class="ticket-desc">{ticket.description.slice(0, 200)}{ticket.description.length > 200 ? '...' : ''}</div>
                {#if ticket.required_output_files.length > 0}
                  <div class="ticket-files">
                    {#each ticket.required_output_files as f}
                      <span class="file-badge">{f}</span>
                    {/each}
                  </div>
                {/if}
                {#if ticket.depends_on.length > 0}
                  <div class="ticket-deps">
                    Depends on: {ticket.depends_on.join(', ')}
                  </div>
                {/if}
              </div>
            {/each}
          </div>
        </div>
      {/each}
    </div>

    <div class="plan-actions">
      <button
        class="btn-approve"
        on:click={commitPlan}
        disabled={committing || disabled}
      >
        {committing ? 'Committing...' : `Approve & Create ${plan.total_tickets} Tickets`}
      </button>
      <button
        class="btn-retry"
        on:click={decompose}
        disabled={decomposing || disabled}
      >
        Re-decompose
      </button>
    </div>
  {/if}
</section>

<style>
  .decomp-section {
    background: var(--bg-card, #16202E);
    border: 1px solid rgba(58, 190, 255, 0.12);
    border-radius: 12px;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .decomp-header {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .section-header {
    font-family: var(--font-ui);
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--color-text-primary, #E6EDF3);
    margin: 0;
  }

  .decomp-hint {
    font-size: 0.75rem;
    color: var(--color-text-muted, #6B7A8D);
    margin: 0;
  }

  /* Error */
  .decomp-error {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px;
    background: rgba(255, 80, 80, 0.1);
    border: 1px solid rgba(255, 80, 80, 0.3);
    border-radius: 6px;
    font-size: 0.8rem;
    color: #FF6B6B;
  }

  .dismiss-btn {
    background: none;
    border: none;
    color: #FF6B6B;
    cursor: pointer;
    padding: 0 4px;
    font-size: 0.85rem;
  }

  /* Loading */
  .decomp-loading {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 20px;
    justify-content: center;
    color: var(--color-text-secondary, #8B9DC3);
    font-size: 0.85rem;
  }

  .spinner {
    width: 18px;
    height: 18px;
    border: 2px solid rgba(58, 190, 255, 0.2);
    border-top-color: var(--color-accent-primary, #3ABEFF);
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  /* Decompose button */
  .btn-decompose {
    background: var(--color-accent-primary, #3ABEFF);
    color: #0B1220;
    border: none;
    border-radius: 8px;
    padding: 14px 24px;
    font-size: 0.9rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 150ms, box-shadow 150ms;
    width: 100%;
  }

  .btn-decompose:hover:not(:disabled) {
    background: #5BCEFF;
    box-shadow: 0 0 16px rgba(58, 190, 255, 0.25);
  }

  .btn-decompose:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  /* Plan summary */
  .plan-summary {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 14px;
    background: rgba(58, 190, 255, 0.06);
    border: 1px solid rgba(58, 190, 255, 0.15);
    border-radius: 8px;
  }

  .summary-stat {
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--color-accent-primary, #3ABEFF);
  }

  .summary-dot {
    color: var(--color-text-muted, #6B7A8D);
  }

  /* Gate groups */
  .gate-list {
    display: flex;
    flex-direction: column;
    gap: 16px;
    max-height: 500px;
    overflow-y: auto;
    padding-right: 4px;
  }

  .gate-header {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--color-text-secondary, #8B9DC3);
    margin: 0 0 8px 0;
    padding-bottom: 6px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  }

  .ticket-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .ticket-card {
    padding: 10px 14px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 8px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .ticket-card.parent {
    border-left: 3px solid var(--color-accent-primary, #3ABEFF);
  }

  .ticket-id {
    font-size: 0.7rem;
    font-weight: 700;
    font-family: var(--font-mono, monospace);
    color: var(--color-accent-primary, #3ABEFF);
    letter-spacing: 0.03em;
  }

  .ticket-desc {
    font-size: 0.8rem;
    line-height: 1.4;
    color: var(--color-text-primary, #E6EDF3);
  }

  .ticket-files {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }

  .file-badge {
    font-size: 0.65rem;
    font-family: var(--font-mono, monospace);
    padding: 2px 6px;
    background: rgba(58, 190, 255, 0.08);
    border: 1px solid rgba(58, 190, 255, 0.15);
    border-radius: 4px;
    color: var(--color-text-secondary, #8B9DC3);
  }

  .ticket-deps {
    font-size: 0.7rem;
    color: var(--color-text-muted, #6B7A8D);
    font-style: italic;
  }

  /* Actions */
  .plan-actions {
    display: flex;
    gap: 10px;
    padding-top: 8px;
  }

  .btn-approve {
    flex: 1;
    background: #3ABE55;
    color: #0B1220;
    border: none;
    border-radius: 8px;
    padding: 12px 20px;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 150ms;
  }

  .btn-approve:hover:not(:disabled) {
    background: #4DD66A;
  }

  .btn-approve:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .btn-retry {
    background: transparent;
    color: var(--color-text-secondary, #8B9DC3);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 0.85rem;
    font-weight: 500;
    cursor: pointer;
    transition: border-color 150ms, color 150ms;
  }

  .btn-retry:hover:not(:disabled) {
    border-color: rgba(255, 255, 255, 0.3);
    color: var(--color-text-primary, #E6EDF3);
  }

  .btn-retry:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style>
