<script lang="ts">
  import { fade, fly } from 'svelte/transition';
  import { ticketDrawerOpen, closeTicketDrawer } from '$lib/stores/drawer';
  import { pipelineStore } from '$lib/stores/pipeline';
  import type { PipelineTicket } from '$lib/stores/pipeline';

  $: open = $ticketDrawerOpen;
  $: state = $pipelineStore;
  $: tickets = state.tickets;
  $: decomposing = state.phase === 'creating';

  interface GateGroup {
    gate: number;
    tickets: PipelineTicket[];
  }

  $: gateGroups = groupByGate(tickets);

  function groupByGate(tickets: PipelineTicket[]): GateGroup[] {
    const groups = new Map<number, PipelineTicket[]>();
    for (const t of tickets) {
      const arr = groups.get(t.gate) ?? [];
      arr.push(t);
      groups.set(t.gate, arr);
    }
    return Array.from(groups.entries())
      .sort((a, b) => a[0] - b[0])
      .map(([gate, tickets]) => ({ gate, tickets }));
  }

  function onKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') closeTicketDrawer();
  }

  function statusLabel(status: string): string {
    switch (status) {
      case 'creating': return 'Generating...';
      case 'coding': return 'Building';
      case 'qa': return 'QA Review';
      case 'done': return 'Complete';
      default: return '';
    }
  }
</script>

<svelte:window on:keydown={onKeydown} />

{#if open}
  <!-- Backdrop -->
  <div class="backdrop" transition:fade={{ duration: 200 }} on:click={closeTicketDrawer}></div>

  <!-- Drawer panel — slides from right -->
  <div class="drawer" transition:fly={{ x: 500, duration: 300, opacity: 1 }}>
    <div class="header">
      <div class="header-left">
        <h2 class="title">Ticket Details</h2>
        <div class="summary">
          <span class="count">{tickets.length} ticket{tickets.length !== 1 ? 's' : ''}</span>
          {#if gateGroups.length > 0}
            <span class="dot">&middot;</span>
            <span class="count">{gateGroups.length} phase{gateGroups.length !== 1 ? 's' : ''}</span>
          {/if}
          {#if decomposing}
            <span class="live-badge">LIVE</span>
          {/if}
        </div>
      </div>
      <button class="close-btn" on:click={closeTicketDrawer} title="Close">
        <svg width="18" height="18" viewBox="0 0 18 18">
          <path d="M4 4 L14 14 M14 4 L4 14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
      </button>
    </div>

    <div class="body">
      {#if tickets.length === 0}
        <div class="empty">
          {#if decomposing}
            <span class="spinner"></span>
            <p>Analyzing PRD and generating tickets...</p>
          {:else}
            <p>No tickets yet. Start a decomposition to see them here.</p>
          {/if}
        </div>
      {:else}
        {#each gateGroups as group}
          <div class="gate-group">
            <div class="gate-header">
              <span class="gate-label">Phase {group.gate}</span>
              <span class="gate-count">{group.tickets.length} ticket{group.tickets.length !== 1 ? 's' : ''}</span>
            </div>
            {#each group.tickets as ticket}
              <div class="ticket-card">
                <div class="ticket-top">
                  <span class="ticket-id">{ticket.id}</span>
                  {#if ticket.is_parent}
                    <span class="parent-badge">parent</span>
                  {/if}
                </div>
                <div class="ticket-desc">{ticket.description.slice(0, 300)}{ticket.description.length > 300 ? '...' : ''}</div>
                {#if ticket.required_output_files.length > 0}
                  <div class="file-row">
                    {#each ticket.required_output_files as f}
                      <span class="file-badge">{f}</span>
                    {/each}
                  </div>
                {/if}
                {#if ticket.depends_on.length > 0}
                  <div class="deps">Depends on: {ticket.depends_on.join(', ')}</div>
                {/if}
              </div>
            {/each}
          </div>
        {/each}
      {/if}
    </div>
  </div>
{/if}

<style>
  .backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 100;
  }

  .drawer {
    position: fixed;
    top: 0;
    right: 0;
    bottom: 0;
    width: min(560px, 90vw);
    background: var(--color-bg-base, #0D1520);
    border-left: 1px solid rgba(255, 255, 255, 0.08);
    box-shadow: -8px 0 40px rgba(0, 0, 0, 0.6);
    z-index: 101;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding: 20px 24px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    flex-shrink: 0;
  }

  .header-left {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .title {
    font-size: 1rem;
    font-weight: 600;
    color: var(--color-text-primary, #E6EDF3);
    margin: 0;
  }

  .summary {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .count {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--color-accent-primary, #3ABEFF);
  }

  .dot {
    color: var(--color-text-muted, #6B7A8D);
  }

  .live-badge {
    font-size: 0.55rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    padding: 2px 8px;
    border-radius: 4px;
    background: rgba(58, 190, 255, 0.15);
    color: var(--color-accent-primary, #3ABEFF);
    animation: pulse-live 1.5s ease-in-out infinite;
  }

  @keyframes pulse-live {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }

  .close-btn {
    background: none;
    border: none;
    color: var(--color-text-muted, #6B7A8D);
    cursor: pointer;
    padding: 4px;
    border-radius: 4px;
    transition: color 0.15s, background-color 0.15s;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .close-btn:hover {
    color: var(--color-text-primary, #E6EDF3);
    background: rgba(255, 255, 255, 0.06);
  }

  .body {
    flex: 1;
    overflow-y: auto;
    padding: 16px 24px;
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  .body::-webkit-scrollbar {
    width: 6px;
  }

  .body::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 3px;
  }

  /* Empty state */
  .empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    padding: 60px 20px;
    color: var(--color-text-muted, #6B7A8D);
    font-size: 0.85rem;
    text-align: center;
  }

  .spinner {
    width: 20px;
    height: 20px;
    border: 2px solid rgba(58, 190, 255, 0.2);
    border-top-color: var(--color-accent-primary, #3ABEFF);
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  /* Gate groups */
  .gate-group {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .gate-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 6px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  }

  .gate-label {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--color-text-secondary, #8B9DC3);
  }

  .gate-count {
    font-size: 0.65rem;
    color: var(--color-text-muted, #6B7A8D);
  }

  /* Ticket cards */
  .ticket-card {
    padding: 12px 14px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 8px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    transition: border-color 0.15s;
  }

  .ticket-card:hover {
    border-color: rgba(255, 255, 255, 0.12);
  }

  .ticket-top {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .ticket-id {
    font-size: 0.7rem;
    font-weight: 700;
    font-family: var(--font-mono, monospace);
    color: var(--color-accent-primary, #3ABEFF);
    letter-spacing: 0.03em;
  }

  .parent-badge {
    font-size: 0.55rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    padding: 1px 6px;
    border-radius: 3px;
    background: rgba(58, 190, 255, 0.1);
    color: var(--color-accent-primary, #3ABEFF);
  }

  .ticket-desc {
    font-size: 0.8rem;
    line-height: 1.45;
    color: var(--color-text-primary, #E6EDF3);
  }

  .file-row {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }

  .file-badge {
    font-size: 0.6rem;
    font-family: var(--font-mono, monospace);
    padding: 2px 6px;
    background: rgba(58, 190, 255, 0.08);
    border: 1px solid rgba(58, 190, 255, 0.15);
    border-radius: 4px;
    color: var(--color-text-secondary, #8B9DC3);
  }

  .deps {
    font-size: 0.65rem;
    color: var(--color-text-muted, #6B7A8D);
    font-style: italic;
  }

  @media (max-width: 768px) {
    .drawer {
      width: 100vw;
    }
  }
</style>
