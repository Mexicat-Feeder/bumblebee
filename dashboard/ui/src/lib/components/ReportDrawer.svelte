<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { fade, fly } from 'svelte/transition';
  import { reportDrawerOpen, closeReportDrawer } from '$lib/stores/drawer';
  import { researchStore } from '$lib/stores/research';
  import type { ResearchTicket } from '$lib/stores/research';
  import { researchStatusColor, researchStatusLabel } from '$lib/stores/research';

  $: open = $reportDrawerOpen;
  $: tickets = $researchStore.tickets ?? [];

  // Selected ticket for report viewing
  let selectedId: string | null = null;
  let reportContent: string | null = null;
  let reportLoading = false;

  // Auto-select the most recent ticket
  $: if (open && tickets.length > 0 && !selectedId) {
    // Pick the most recently completed, or first in list
    const complete = tickets.find((t: ResearchTicket) => t.display_status === 'complete');
    selectedId = complete?.id ?? tickets[0]?.id ?? null;
  }

  // Fetch report when selection changes
  $: if (selectedId && open) {
    fetchReport(selectedId);
  }

  async function fetchReport(id: string) {
    reportLoading = true;
    reportContent = null;
    try {
      const res = await fetch(`/api/research/tickets/${id}/report`);
      if (res.ok) {
        const data = await res.json();
        reportContent = data.content ?? null;
      }
    } catch { /* keep null */ }
    reportLoading = false;
  }

  function selectTicket(id: string) {
    selectedId = id;
  }

  function onClose() {
    selectedId = null;
    reportContent = null;
    closeReportDrawer();
  }

  function onKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') onClose();
  }

  function fmtDate(iso: string | null): string {
    if (!iso) return '';
    return new Date(iso).toLocaleDateString('en-US', {
      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
    });
  }
</script>

<svelte:window on:keydown={onKeydown} />

{#if open}
  <div class="backdrop" transition:fade={{ duration: 200 }} on:click={onClose} role="presentation"></div>

  <div class="drawer" transition:fly={{ x: 500, duration: 300, opacity: 1 }}>
    <div class="header">
      <div class="header-left">
        <h2 class="title">Research Reports</h2>
        <span class="subtitle">{tickets.length} ticket{tickets.length !== 1 ? 's' : ''}</span>
      </div>
      <button class="close-btn" on:click={onClose} title="Close">
        <svg width="18" height="18" viewBox="0 0 18 18">
          <path d="M4 4 L14 14 M14 4 L4 14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
      </button>
    </div>

    <div class="body">
      {#if tickets.length === 0}
        <div class="empty">
          <p>No research tickets yet. Submit one from the Sift row.</p>
        </div>
      {:else}
        <!-- Ticket tabs -->
        <div class="ticket-tabs">
          {#each tickets as t (t.id)}
            <button
              class="tab"
              class:active={selectedId === t.id}
              on:click={() => selectTicket(t.id)}
            >
              <span class="tab-id">{t.id}</span>
              <span class="tab-dot" style="background: {researchStatusColor(t.display_status)}"></span>
              <span class="tab-status">{researchStatusLabel(t.display_status, t.queue_status)}</span>
            </button>
          {/each}
        </div>

        <!-- Selected ticket detail -->
        {#if selectedId}
          {@const ticket = tickets.find((t) => t.id === selectedId)}
          {#if ticket}
            <div class="ticket-header">
              <span class="ticket-id">{ticket.id}</span>
              <span class="status-pill" style="background: {researchStatusColor(ticket.display_status)}22; color: {researchStatusColor(ticket.display_status)}; border: 1px solid {researchStatusColor(ticket.display_status)}44">
                {researchStatusLabel(ticket.display_status, ticket.queue_status)}
              </span>
              {#if ticket.enqueued_at}
                <span class="ticket-date">{fmtDate(ticket.enqueued_at)}</span>
              {/if}
            </div>
            <p class="ticket-question">{ticket.ticket_description ?? '(no description)'}</p>

            <div class="report-section">
              {#if reportLoading}
                <div class="report-loading">
                  <span class="spinner"></span>
                  Loading report...
                </div>
              {:else if reportContent}
                <pre class="report-body">{reportContent}</pre>
              {:else if ticket.display_status === 'complete'}
                <div class="report-pending">Report file not found.</div>
              {:else if ticket.display_status === 'in_progress'}
                <div class="report-pending">
                  <span class="spinner"></span>
                  <p>Sift is working on this report...</p>
                  <p class="pending-sub">This view updates automatically.</p>
                </div>
              {:else}
                <div class="report-pending">
                  <p>Queued. Sift will pick this up shortly.</p>
                </div>
              {/if}
            </div>
          {/if}
        {/if}
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
    width: min(640px, 92vw);
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
    gap: 4px;
  }

  .title {
    font-size: 1rem;
    font-weight: 600;
    color: var(--color-text-primary, #E6EDF3);
    margin: 0;
  }

  .subtitle {
    font-size: 0.7rem;
    color: var(--color-text-muted, #6B7A8D);
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
    gap: 16px;
  }

  .body::-webkit-scrollbar { width: 6px; }
  .body::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.1); border-radius: 3px; }

  .empty {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 60px 20px;
    color: var(--color-text-muted, #6B7A8D);
    font-size: 0.85rem;
    text-align: center;
  }

  /* Ticket tabs */
  .ticket-tabs {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
  }

  .tab {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 6px;
    color: var(--color-text-secondary, #8B9DC3);
    font-family: var(--font-ui);
    font-size: 0.7rem;
    cursor: pointer;
    transition: border-color 0.15s, background 0.15s;
  }

  .tab:hover {
    border-color: rgba(255, 255, 255, 0.15);
    background: rgba(255, 255, 255, 0.06);
  }

  .tab.active {
    border-color: var(--color-accent-primary, #3ABEFF);
    background: rgba(58, 190, 255, 0.08);
    color: var(--color-text-primary, #E6EDF3);
  }

  .tab-id {
    font-family: var(--font-mono, monospace);
    font-weight: 600;
    font-size: 0.65rem;
  }

  .tab-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .tab-status {
    font-size: 0.6rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }

  /* Ticket header */
  .ticket-header {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
  }

  .ticket-id {
    font-size: 0.7rem;
    font-weight: 700;
    font-family: var(--font-mono, monospace);
    color: var(--color-text-muted, #6B7A8D);
    letter-spacing: 0.05em;
  }

  .status-pill {
    font-size: 0.6rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    padding: 2px 10px;
    border-radius: 20px;
  }

  .ticket-date {
    font-size: 0.65rem;
    color: var(--color-text-muted, #6B7A8D);
  }

  .ticket-question {
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--color-text-primary, #E6EDF3);
    margin: 0;
    line-height: 1.4;
  }

  /* Report */
  .report-section {
    flex: 1;
    display: flex;
    flex-direction: column;
  }

  .report-loading {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 20px;
    color: var(--color-text-muted, #6B7A8D);
    font-size: 0.8rem;
    justify-content: center;
  }

  .report-body {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 8px;
    padding: 20px 24px;
    font-family: var(--font-mono, monospace);
    font-size: 0.78rem;
    color: var(--color-text-secondary, #8B9DC3);
    line-height: 1.7;
    white-space: pre-wrap;
    word-break: break-word;
    margin: 0;
    overflow-x: auto;
  }

  .report-pending {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    padding: 40px 20px;
    text-align: center;
    color: var(--color-text-muted, #6B7A8D);
    font-size: 0.85rem;
  }

  .report-pending p { margin: 0; }
  .pending-sub { font-size: 0.75rem; opacity: 0.7; }

  .spinner {
    width: 18px;
    height: 18px;
    border: 2px solid rgba(58, 190, 255, 0.2);
    border-top-color: var(--color-accent-primary, #3ABEFF);
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
  }

  @keyframes spin { to { transform: rotate(360deg); } }

  @media (max-width: 768px) {
    .drawer { width: 100vw; }
  }
</style>
