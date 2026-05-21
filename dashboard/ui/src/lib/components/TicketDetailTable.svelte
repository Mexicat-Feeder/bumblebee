<script lang="ts">
  import { ticketStore } from '$lib/stores/tickets';
  export let selectedGate: number | null = null;
  $: gateTickets = selectedGate !== null
    ? $ticketStore.tickets.filter(t => t.gate === selectedGate)
    : [];

  function statusClass(status: string): string {
    if (status === 'qa_verified') return 'badge--pass';
    if (status === 'in_progress') return 'badge--running';
    if (status === 'blocked') return 'badge--fail';
    return 'badge--muted';
  }
</script>

{#if selectedGate === null}
  <p class="empty-msg">Select a gate to view tickets</p>
{:else if gateTickets.length === 0}
  <p class="empty-msg">No tickets in gate {selectedGate}</p>
{:else}
  <table class="ticket-table">
    <thead>
      <tr>
        <th>Ticket ID</th>
        <th>Status</th>
        <th>Assignee</th>
        <th>Updated</th>
      </tr>
    </thead>
    <tbody>
      {#each gateTickets as t}
        <tr>
          <td class="ticket-id">{t.id}</td>
          <td><span class="badge {statusClass(t.status)}">{t.status}</span></td>
          <td class="assignee">{t.assignee ?? '—'}</td>
          <td class="updated">{t.updated_at ?? '—'}</td>
        </tr>
      {/each}
    </tbody>
  </table>
{/if}

<style>
  .empty-msg {
    color: var(--color-text-muted);
    font-size: var(--text-body);
    padding: var(--spacing-panel-pad);
  }
  .ticket-table {
    width: 100%;
    border-collapse: collapse;
    font-size: var(--text-body);
  }
  .ticket-table th {
    text-align: left;
    font-size: var(--text-kpi-label);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--color-text-muted);
    padding: 6px 12px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  }
  .ticket-table tr {
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  }
  .ticket-table td {
    padding: 8px 12px;
    color: var(--color-text-primary);
  }
  .ticket-id {
    font-family: var(--font-mono);
    font-size: var(--text-badge);
  }
  .assignee, .updated {
    color: var(--color-text-muted);
    font-size: var(--text-badge);
  }
  .badge {
    font-size: var(--text-badge);
    text-transform: uppercase;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: var(--radius-badge);
    display: inline-block;
  }
  .badge--pass    { background: var(--color-status-pass); color: #fff; }
  .badge--running { background: var(--color-status-running); color: #fff; }
  .badge--fail    { background: var(--color-status-fail); color: #fff; }
  .badge--muted   { background: rgba(255,255,255,0.1); color: var(--color-text-muted); }
</style>
