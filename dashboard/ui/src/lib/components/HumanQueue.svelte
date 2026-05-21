<script lang="ts">
  import { tick } from 'svelte';
  import { get } from 'svelte/store';
  import { ticketStore } from '$lib/stores/tickets';

  interface Ticket {
    id: string;
    status: string;
    blocked_reason_code?: string;
    created_at: string;
  }

  function getHumanBlockedTickets(): Ticket[] {
    const state = get(ticketStore);
    if (!state || !Array.isArray(state.tickets)) return [];
    return state.tickets.filter(
      (t: Ticket) =>
        t.status === 'blocked' &&
        t.blocked_reason_code &&
        t.blocked_reason_code.toLowerCase().includes('human'),
    );
  }

  let humanTickets: Ticket[] = [];

  function refresh() {
    humanTickets = getHumanBlockedTickets();
  }

  refresh();

  // Poll every 10s for new human-queued tickets
  const intervalId = setInterval(refresh, 10_000);

  function formatRelativeTime(dateStr: string): string {
    const now = Date.now();
    const then = new Date(dateStr).getTime();
    const diff = now - then;
    const minutes = Math.floor(diff / 60_000);
    const hours = Math.floor(minutes / 60);

    if (minutes < 1) return 'just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  }
</script>

<div class="panel">
  <h3 class="section-title">Human Queue</h3>

  {#if humanTickets.length === 0}
    <p class="empty-state">No human-blocked tickets</p>
  {:else}
    <div class="ticket-list">
      {#each humanTickets as ticket (ticket.id)}
        <div class="ticket-item">
          <span class="ticket-id">{ticket.id}</span>
          <span class="ticket-time">{formatRelativeTime(ticket.created_at)}</span>
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .panel {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .section-title {
    font-size: var(--text-section);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--color-text-secondary);
    font-weight: 600;
    margin: 0;
  }

  .empty-state {
    font-size: var(--text-body);
    color: var(--color-text-muted);
    font-style: italic;
    margin: 0;
  }

  .ticket-list {
    display: flex;
    flex-direction: column;
    gap: 0;
  }

  .ticket-item {
    display: flex;
    justify-content: space-between;
    padding: 6px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  }

  .ticket-item:last-child {
    border-bottom: none;
  }

  .ticket-id {
    font-family: var(--font-mono);
    font-size: var(--text-badge);
    color: var(--color-text-primary);
  }

  .ticket-time {
    font-size: var(--text-badge);
    color: var(--color-text-muted);
  }
</style>
