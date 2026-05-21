<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { researchStatusColor, researchStatusLabel } from '$lib/stores/research';

  export let ticketId: string;

  interface TicketDetail {
    id: string;
    ticket_description: string | null;
    queue_status: string | null;
    display_status: string;
    priority: number | null;
    enqueued_at: string | null;
    last_attempt_at: string | null;
    last_note: string | null;
    attempt_count: number;
    report_path: string | null;
  }

  let ticket: TicketDetail | null = null;
  let reportContent: string | null = null;
  let loading = true;
  let interval: ReturnType<typeof setInterval> | null = null;

  async function fetchAll() {
    try {
      const [tr, rr] = await Promise.all([
        fetch(`/api/research/tickets/${ticketId}`),
        fetch(`/api/research/tickets/${ticketId}/report`),
      ]);
      if (tr.ok) ticket = await tr.json();
      if (rr.ok) {
        const rd = await rr.json();
        reportContent = rd.content ?? null;
      }
    } catch { /* keep last */ }
    finally { loading = false; }
  }

  onMount(() => {
    fetchAll();
    // Poll more frequently when not yet complete
    interval = setInterval(fetchAll, 10000);
  });
  onDestroy(() => { if (interval) clearInterval(interval); });

  $: isComplete = ticket?.display_status === 'complete';
  $: statusColor = ticket ? researchStatusColor(ticket.display_status) : '#888';
  $: statusLabel = ticket ? researchStatusLabel(ticket.display_status, ticket.queue_status) : '';

  function fmtDate(iso: string | null): string {
    if (!iso) return '—';
    return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  }
</script>

<div class="report-view">
  {#if loading}
    <div class="loading">Loading…</div>
  {:else if !ticket}
    <div class="unavailable">Ticket {ticketId} not found.</div>
  {:else}
    <!-- Header -->
    <div class="report-header">
      <div class="title-row">
        <span class="ticket-id">{ticket.id}</span>
        <span class="status-pill" style="background: {statusColor}22; color: {statusColor}; border: 1px solid {statusColor}44">
          {statusLabel}
        </span>
      </div>
      <p class="question-text">{ticket.ticket_description ?? '(no description)'}</p>
    </div>

    <!-- Meta row -->
    <div class="meta-row">
      <span class="meta-item">Submitted {fmtDate(ticket.enqueued_at)}</span>
      {#if ticket.last_attempt_at}
        <span class="meta-sep">·</span>
        <span class="meta-item">Last run {fmtDate(ticket.last_attempt_at)}</span>
      {/if}
      {#if ticket.attempt_count}
        <span class="meta-sep">·</span>
        <span class="meta-item">{ticket.attempt_count} attempt{ticket.attempt_count !== 1 ? 's' : ''}</span>
      {/if}
    </div>

    <!-- Last note -->
    {#if ticket.last_note}
      <div class="note-card">
        <span class="note-label">Latest note</span>
        <p class="note-text">{ticket.last_note}</p>
      </div>
    {/if}

    <!-- Report -->
    <div class="report-section">
      <h2 class="section-heading">Report</h2>
      {#if reportContent}
        <pre class="report-body">{reportContent}</pre>
      {:else if isComplete}
        <div class="unavailable">Report marked complete but file not found at:<br><code>{ticket.report_path}</code></div>
      {:else}
        <div class="pending-report">
          <div class="pending-icon">📋</div>
          <p>Report not yet available. Pixel is working on it.</p>
          <p class="pending-sub">This view will update automatically.</p>
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .report-view {
    max-width: 800px;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    gap: 16px;
    padding-bottom: 40px;
  }

  .loading, .unavailable {
    color: var(--color-text-muted);
    font-size: 13px;
    padding: 40px 0;
    text-align: center;
  }

  .report-header {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .title-row {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
  }

  .ticket-id {
    font-size: 13px;
    font-weight: 700;
    font-family: var(--font-mono);
    color: var(--color-text-muted);
    letter-spacing: 0.05em;
  }

  .status-pill {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    padding: 2px 10px;
    border-radius: 20px;
  }

  .question-text {
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--color-text-primary);
    margin: 0;
    line-height: 1.4;
  }

  .meta-row {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
  }

  .meta-item {
    font-size: 12px;
    color: var(--color-text-muted);
  }

  .meta-sep {
    color: var(--color-text-muted);
    opacity: 0.4;
  }

  .note-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 8px;
    padding: 12px 16px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .note-label {
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--color-text-muted);
  }

  .note-text {
    font-size: 13px;
    color: var(--color-text-secondary);
    margin: 0;
    line-height: 1.5;
    white-space: pre-wrap;
  }

  .report-section {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .section-heading {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--color-text-muted);
    margin: 0;
  }

  .report-body {
    background: var(--color-bg-panel);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 8px;
    padding: 20px 24px;
    font-family: var(--font-mono);
    font-size: 13px;
    color: var(--color-text-secondary);
    line-height: 1.7;
    white-space: pre-wrap;
    word-break: break-word;
    margin: 0;
    overflow-x: auto;
  }

  .pending-report {
    background: var(--color-bg-panel);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 8px;
    padding: 40px 24px;
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
  }

  .pending-icon { font-size: 32px; }

  .pending-report p {
    margin: 0;
    font-size: 14px;
    color: var(--color-text-secondary);
  }

  .pending-sub { font-size: 12px; color: var(--color-text-muted) !important; }
</style>
