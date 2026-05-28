<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { fade, fly } from 'svelte/transition';
  import { codingDrawerOpen, closeCodingDrawer } from '$lib/stores/drawer';
  import { pipelineStore } from '$lib/stores/pipeline';

  export let slug: string = '';

  $: open = $codingDrawerOpen;
  $: state = $pipelineStore;

  let logLines: string[] = [];
  let ticketStats: Record<string, number> = {};
  let executorRunning = false;
  let logInterval: ReturnType<typeof setInterval> | null = null;
  let logEl: HTMLPreElement;
  let autoScroll = true;

  async function fetchLogs() {
    if (!slug) return;
    try {
      const [logRes, statusRes] = await Promise.all([
        fetch(`/api/projects/${slug}/executor/logs?lines=200`),
        fetch(`/api/projects/${slug}/executor/status`),
      ]);
      if (logRes.ok) {
        const d = await logRes.json();
        logLines = d.lines ?? [];
      }
      if (statusRes.ok) {
        const d = await statusRes.json();
        executorRunning = d.running ?? false;
        ticketStats = d.ticket_stats ?? {};
      }
    } catch { /* keep last */ }
  }

  $: if (open && slug) {
    fetchLogs();
    if (!logInterval) {
      logInterval = setInterval(fetchLogs, 2000);
    }
  }

  $: if (!open && logInterval) {
    clearInterval(logInterval);
    logInterval = null;
  }

  // Auto-scroll to bottom when new log lines arrive
  $: if (logLines.length && logEl && autoScroll) {
    requestAnimationFrame(() => {
      if (logEl) logEl.scrollTop = logEl.scrollHeight;
    });
  }

  function onClose() {
    closeCodingDrawer();
  }

  function onKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') onClose();
  }

  function statusSummary(stats: Record<string, number>): string {
    const parts: string[] = [];
    if (stats['todo']) parts.push(`${stats['todo']} todo`);
    if (stats['in_progress']) parts.push(`${stats['in_progress']} building`);
    if (stats['done']) parts.push(`${stats['done']} done`);
    if (stats['qa_verified']) parts.push(`${stats['qa_verified']} verified`);
    if (stats['blocked']) parts.push(`${stats['blocked']} blocked`);
    return parts.join(' / ') || 'No tickets';
  }

  onDestroy(() => {
    if (logInterval) { clearInterval(logInterval); logInterval = null; }
  });
</script>

<svelte:window on:keydown={onKeydown} />

{#if open}
  <div class="backdrop" transition:fade={{ duration: 200 }} on:click={onClose} role="presentation"></div>

  <div class="drawer" transition:fly={{ x: 500, duration: 300, opacity: 1 }}>
    <div class="header">
      <div class="header-left">
        <h2 class="title">Build Log</h2>
        <div class="header-meta">
          <span class="status-dot" class:running={executorRunning} class:stopped={!executorRunning}></span>
          <span class="status-label">{executorRunning ? 'Executor running' : 'Executor stopped'}</span>
        </div>
      </div>
      <button class="close-btn" on:click={onClose} title="Close">
        <svg width="18" height="18" viewBox="0 0 18 18">
          <path d="M4 4 L14 14 M14 4 L4 14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
      </button>
    </div>

    <!-- Ticket stats bar -->
    <div class="stats-bar">
      <span class="stats-text">{statusSummary(ticketStats)}</span>
    </div>

    <!-- Log output -->
    <pre
      class="log-body"
      bind:this={logEl}
      on:scroll={() => {
        if (logEl) {
          const atBottom = logEl.scrollHeight - logEl.scrollTop - logEl.clientHeight < 40;
          autoScroll = atBottom;
        }
      }}
    >{#if logLines.length > 0}{logLines.join('\n')}{:else}No log output yet.{/if}</pre>
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
    width: min(700px, 92vw);
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
    padding: 16px 20px;
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

  .header-meta {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .status-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
  }

  .status-dot.running {
    background: #59e38a;
    animation: pulse-dot 2s ease-in-out infinite;
  }

  .status-dot.stopped {
    background: #6B7A8D;
  }

  @keyframes pulse-dot {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
  }

  .status-label {
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
    display: flex;
  }

  .close-btn:hover {
    color: var(--color-text-primary, #E6EDF3);
    background: rgba(255, 255, 255, 0.06);
  }

  .stats-bar {
    padding: 8px 20px;
    background: rgba(255, 255, 255, 0.03);
    border-bottom: 1px solid rgba(255, 255, 255, 0.04);
    flex-shrink: 0;
  }

  .stats-text {
    font-size: 0.7rem;
    font-family: var(--font-mono, monospace);
    color: var(--color-text-secondary, #8B9DC3);
  }

  .log-body {
    flex: 1;
    overflow-y: auto;
    padding: 12px 20px;
    margin: 0;
    font-family: var(--font-mono, monospace);
    font-size: 0.72rem;
    line-height: 1.6;
    color: var(--color-text-secondary, #8B9DC3);
    white-space: pre-wrap;
    word-break: break-all;
    background: rgba(0, 0, 0, 0.2);
  }

  .log-body::-webkit-scrollbar { width: 6px; }
  .log-body::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.1); border-radius: 3px; }

  @media (max-width: 768px) {
    .drawer { width: 100vw; }
  }
</style>
