<script lang="ts">
  import { ticketStore } from '$lib/stores/tickets';
  import { selectedProject } from '$lib/stores/projects';

  // Derive the current project slug for detail fetches
  $: slug = $selectedProject?.slug ?? 'dashboard';

  // Sort tickets by updated_at descending for dispatch-log feel
  $: tickets = [...($ticketStore.tickets ?? [])].sort(
    (a, b) => (b.updated_at ?? '').localeCompare(a.updated_at ?? '')
  );

  // Selected ticket id + detail data
  let selectedId: string | null = null;
  let detail: Record<string, any> | null = null;
  let detailLoading = false;
  let detailError: string | null = null;

  async function selectTicket(id: string) {
    if (selectedId === id) {
      // Toggle off
      selectedId = null;
      detail = null;
      return;
    }
    selectedId = id;
    detail = null;
    detailError = null;
    detailLoading = true;
    try {
      const res = await fetch(`/api/tickets/${slug}/${id}/detail`);
      const data = await res.json();
      if (data.error) { detailError = data.error; detail = null; }
      else detail = data;
    } catch (e: any) {
      detailError = e.message ?? 'Failed to load detail';
    }
    detailLoading = false;
  }

  function badgeClass(status: string): string {
    const s = (status ?? '').toLowerCase();
    if (s === 'qa_verified') return 'badge-pass';
    if (s === 'blocked' || s === 'failed') return 'badge-fail';
    if (s === 'in_progress') return 'badge-running';
    if (s === 'todo' || s === 'queued') return 'badge-todo';
    return 'badge-default';
  }

  function fmtTime(ts: string | null): string {
    if (!ts) return '—';
    try {
      const d = new Date(ts);
      return d.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    } catch { return ts; }
  }

  function fmtDetailValue(key: string, val: any): string {
    if (val === null || val === undefined) return '—';
    if (typeof val === 'string' && (key.endsWith('_json') || val.startsWith('['))) {
      try {
        const parsed = JSON.parse(val);
        if (Array.isArray(parsed) && parsed.length === 0) return '—';
        return JSON.stringify(parsed, null, 2);
      } catch { return val; }
    }
    return String(val);
  }

  // Fields to show in the detail panel (ordered, labelled)
  const DETAIL_FIELDS: [string, string][] = [
    ['ticket_description', 'Description'],
    ['status', 'Status'],
    ['gate', 'Gate'],
    ['assignee', 'Assignee'],
    ['parent_ticket_id', 'Parent'],
    ['failure_count', 'Failures'],
    ['blocked_reason_code', 'Block reason'],
    ['updated_at', 'Updated'],
    ['worker_done_criteria', 'Done when'],
    ['qa_done_criteria', 'QA criteria'],
    ['required_output_files_json', 'Output files'],
    ['context_files_json', 'Context files'],
  ];
</script>

<div class="panel">
  <h3 class="section-title">Dispatch Table</h3>

  {#if $ticketStore.loading}
    <p class="empty-state">Loading…</p>
  {:else if $ticketStore.error}
    <p class="empty-state error">{$ticketStore.error}</p>
  {:else if tickets.length === 0}
    <p class="empty-state">No tickets for this project</p>
  {:else}
    <!-- Scrollable table -->
    <div class="table-scroll">
      <table class="dispatch-table">
        <thead>
          <tr>
            <th>Ticket</th>
            <th>Status</th>
            <th>Gate</th>
            <th>Updated</th>
          </tr>
        </thead>
        <tbody>
          {#each tickets as ticket (ticket.id)}
            <tr
              class="ticket-row"
              class:selected={selectedId === ticket.id}
              on:click={() => selectTicket(ticket.id)}
            >
              <td class="col-ticket">{ticket.id}</td>
              <td class="col-status">
                <span class="badge {badgeClass(ticket.status)}">{ticket.status}</span>
              </td>
              <td class="col-gate">{ticket.gate ?? '—'}</td>
              <td class="col-time">{fmtTime(ticket.updated_at)}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>

    <!-- Detail panel -->
    {#if selectedId}
      <div class="detail-panel">
        <div class="detail-header">
          <span class="detail-id">{selectedId}</span>
          <button class="detail-close" on:click={() => { selectedId = null; detail = null; }}>✕</button>
        </div>

        {#if detailLoading}
          <div class="detail-loading">Loading…</div>
        {:else if detailError}
          <div class="detail-error">{detailError}</div>
        {:else if detail}
          <div class="detail-fields">
            {#each DETAIL_FIELDS as [key, label]}
              {#if detail[key] !== null && detail[key] !== undefined && detail[key] !== '' && detail[key] !== '[]'}
                <div class="detail-row">
                  <span class="detail-label">{label}</span>
                  <pre class="detail-value">{fmtDetailValue(key, detail[key])}</pre>
                </div>
              {/if}
            {/each}
          </div>
        {/if}
      </div>
    {/if}
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

  .empty-state.error { color: var(--color-status-fail); }

  /* Scrollable table container — ~25 rows */
  .table-scroll {
    overflow-y: auto;
    height: 420px;
    border-radius: var(--radius-badge);
    border: 1px solid rgba(255,255,255,0.06);
  }

  .dispatch-table {
    width: 100%;
    border-collapse: collapse;
  }

  .dispatch-table thead {
    position: sticky;
    top: 0;
    background: var(--color-bg-panel);
    z-index: 1;
  }

  .dispatch-table thead tr {
    font-size: var(--text-badge);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--color-text-muted);
    border-bottom: 1px solid rgba(255,255,255,0.08);
  }

  .dispatch-table thead th {
    padding: 8px 10px;
    text-align: left;
    font-weight: 600;
  }

  .ticket-row {
    font-size: var(--text-body);
    border-bottom: 1px solid rgba(255,255,255,0.04);
    cursor: pointer;
    transition: background 0.1s;
  }

  .ticket-row:hover { background: rgba(255,255,255,0.04); }
  .ticket-row.selected { background: rgba(58,190,255,0.08); }
  .ticket-row:last-child { border-bottom: none; }

  .ticket-row td { padding: 7px 10px; }

  .col-ticket {
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--color-text-primary);
  }

  .col-gate {
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--color-text-muted);
  }

  .col-time {
    font-family: var(--font-mono);
    font-size: var(--text-badge);
    color: var(--color-text-muted);
    white-space: nowrap;
  }

  .badge {
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    padding: 2px 7px;
    border-radius: var(--radius-badge);
    display: inline-block;
    white-space: nowrap;
  }

  .badge-pass    { background: rgba(89,227,138,0.15);  color: var(--color-status-pass); }
  .badge-fail    { background: rgba(255,107,107,0.15); color: var(--color-status-fail); }
  .badge-running { background: rgba(58,190,255,0.15);  color: var(--color-accent-primary); }
  .badge-todo    { background: rgba(255,255,255,0.06); color: var(--color-text-muted); }
  .badge-default { background: rgba(255,255,255,0.06); color: var(--color-text-secondary); }

  /* Detail panel */
  .detail-panel {
    background: var(--color-bg-terminal, #0d1117);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: var(--radius-badge);
    padding: 14px 16px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    max-height: 320px;
    overflow-y: auto;
  }

  .detail-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .detail-id {
    font-family: var(--font-mono);
    font-size: 12px;
    font-weight: 700;
    color: var(--color-accent-primary);
    letter-spacing: 0.05em;
  }

  .detail-close {
    background: none;
    border: none;
    color: var(--color-text-muted);
    font-size: 14px;
    cursor: pointer;
    padding: 0;
    line-height: 1;
    transition: color 0.15s;
  }

  .detail-close:hover { color: var(--color-text-primary); }

  .detail-loading, .detail-error {
    font-size: 13px;
    color: var(--color-text-muted);
    font-style: italic;
  }

  .detail-error { color: var(--color-status-fail); }

  .detail-fields {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .detail-row {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .detail-label {
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: var(--color-text-muted);
  }

  .detail-value {
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--color-text-secondary);
    margin: 0;
    white-space: pre-wrap;
    word-break: break-word;
    line-height: 1.5;
  }
</style>
