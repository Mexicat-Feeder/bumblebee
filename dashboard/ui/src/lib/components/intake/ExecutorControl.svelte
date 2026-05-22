<script lang="ts">
  import { onMount, onDestroy } from 'svelte';

  export let slug: string;

  let running = false;
  let pid: number | null = null;
  let startedAt: string | null = null;
  let ticketStats: Record<string, number> = {};
  let logLines: string[] = [];
  let loading = false;
  let error = '';
  let showLogs = false;
  let pollTimer: ReturnType<typeof setInterval> | null = null;

  onMount(() => {
    fetchStatus();
    pollTimer = setInterval(fetchStatus, 5000);
  });

  onDestroy(() => {
    if (pollTimer) clearInterval(pollTimer);
  });

  async function fetchStatus() {
    try {
      const resp = await fetch(`/api/projects/${slug}/executor/status`);
      if (resp.ok) {
        const data = await resp.json();
        running = data.running;
        pid = data.pid;
        startedAt = data.started_at;
        ticketStats = data.ticket_stats || {};
      }
    } catch { /* silent */ }

    if (showLogs) {
      fetchLogs();
    }
  }

  async function fetchLogs() {
    try {
      const resp = await fetch(`/api/projects/${slug}/executor/logs?lines=30`);
      if (resp.ok) {
        const data = await resp.json();
        logLines = data.lines || [];
      }
    } catch { /* silent */ }
  }

  async function startExecutor() {
    loading = true;
    error = '';
    try {
      const resp = await fetch(`/api/projects/${slug}/executor/start`, { method: 'POST' });
      if (!resp.ok) {
        const data = await resp.json().catch(() => ({ detail: resp.statusText }));
        throw new Error(data.detail || `HTTP ${resp.status}`);
      }
      await fetchStatus();
    } catch (e: any) {
      error = e.message || 'Failed to start executor';
    }
    loading = false;
  }

  async function stopExecutor() {
    loading = true;
    error = '';
    try {
      const resp = await fetch(`/api/projects/${slug}/executor/stop`, { method: 'POST' });
      if (!resp.ok) {
        const data = await resp.json().catch(() => ({ detail: resp.statusText }));
        throw new Error(data.detail || `HTTP ${resp.status}`);
      }
      await fetchStatus();
    } catch (e: any) {
      error = e.message || 'Failed to stop executor';
    }
    loading = false;
  }

  $: totalTickets = Object.values(ticketStats).reduce((a, b) => a + b, 0);
  $: completed = (ticketStats['qa_verified'] ?? 0) + (ticketStats['done'] ?? 0);
  $: inProgress = ticketStats['in_progress'] ?? 0;
  $: blocked = ticketStats['blocked'] ?? 0;
  $: progressPct = totalTickets > 0 ? Math.round((completed / totalTickets) * 100) : 0;
</script>

<section class="executor-section">
  <div class="executor-header">
    <h2 class="section-header">CODING ENGINE</h2>
    <div class="status-badge" class:running class:stopped={!running}>
      <span class="status-dot"></span>
      {running ? 'Running' : 'Stopped'}
    </div>
  </div>

  {#if error}
    <div class="exec-error">
      <span>⚠ {error}</span>
      <button class="dismiss-btn" on:click={() => error = ''}>✕</button>
    </div>
  {/if}

  <!-- Progress bar -->
  {#if totalTickets > 0}
    <div class="progress-section">
      <div class="progress-bar">
        <div class="progress-fill" style="width: {progressPct}%"></div>
      </div>
      <div class="progress-stats">
        <span class="stat">{completed}/{totalTickets} completed ({progressPct}%)</span>
        {#if inProgress > 0}
          <span class="stat active">⚡ {inProgress} in progress</span>
        {/if}
        {#if blocked > 0}
          <span class="stat blocked">⏸ {blocked} blocked</span>
        {/if}
      </div>
    </div>
  {/if}

  <!-- Controls -->
  <div class="controls">
    {#if !running}
      <button
        class="btn-start"
        on:click={startExecutor}
        disabled={loading}
      >
        {loading ? 'Starting...' : '▶ Start Coding'}
      </button>
    {:else}
      <button
        class="btn-stop"
        on:click={stopExecutor}
        disabled={loading}
      >
        {loading ? 'Stopping...' : '■ Stop'}
      </button>
    {/if}
    <button
      class="btn-logs"
      on:click={() => { showLogs = !showLogs; if (showLogs) fetchLogs(); }}
    >
      {showLogs ? 'Hide Logs' : 'Show Logs'}
    </button>
  </div>

  <!-- Log viewer -->
  {#if showLogs}
    <div class="log-viewer">
      {#if logLines.length === 0}
        <span class="log-empty">No log output yet.</span>
      {:else}
        {#each logLines as line}
          <div class="log-line">{line}</div>
        {/each}
      {/if}
    </div>
  {/if}
</section>

<style>
  .executor-section {
    background: var(--bg-card, #16202E);
    border: 1px solid rgba(58, 190, 255, 0.12);
    border-radius: 12px;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .executor-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
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

  .status-badge {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 20px;
  }

  .status-badge.running {
    background: rgba(58, 190, 85, 0.12);
    color: #3ABE55;
    border: 1px solid rgba(58, 190, 85, 0.3);
  }

  .status-badge.stopped {
    background: rgba(255, 255, 255, 0.05);
    color: var(--color-text-muted, #6B7A8D);
    border: 1px solid rgba(255, 255, 255, 0.1);
  }

  .status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
  }

  .status-badge.running .status-dot {
    background: #3ABE55;
    box-shadow: 0 0 6px rgba(58, 190, 85, 0.5);
  }

  .status-badge.stopped .status-dot {
    background: #6B7A8D;
  }

  /* Error */
  .exec-error {
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
  }

  /* Progress */
  .progress-section {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .progress-bar {
    height: 6px;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 3px;
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #3ABE55, #4DD66A);
    border-radius: 3px;
    transition: width 0.5s ease;
  }

  .progress-stats {
    display: flex;
    gap: 14px;
    flex-wrap: wrap;
  }

  .stat {
    font-size: 0.75rem;
    color: var(--color-text-secondary, #8B9DC3);
  }

  .stat.active { color: var(--color-accent-primary, #3ABEFF); }
  .stat.blocked { color: #F0B429; }

  /* Controls */
  .controls {
    display: flex;
    gap: 8px;
  }

  .btn-start {
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

  .btn-start:hover:not(:disabled) { background: #4DD66A; }
  .btn-start:disabled { opacity: 0.5; cursor: not-allowed; }

  .btn-stop {
    flex: 1;
    background: rgba(255, 80, 80, 0.15);
    color: #FF6B6B;
    border: 1px solid rgba(255, 80, 80, 0.3);
    border-radius: 8px;
    padding: 12px 20px;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 150ms;
  }

  .btn-stop:hover:not(:disabled) { background: rgba(255, 80, 80, 0.25); }
  .btn-stop:disabled { opacity: 0.5; cursor: not-allowed; }

  .btn-logs {
    background: transparent;
    color: var(--color-text-secondary, #8B9DC3);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 0.85rem;
    cursor: pointer;
    transition: border-color 150ms;
  }

  .btn-logs:hover { border-color: rgba(255, 255, 255, 0.25); }

  /* Log viewer */
  .log-viewer {
    max-height: 300px;
    overflow-y: auto;
    background: rgba(0, 0, 0, 0.25);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 8px;
    padding: 12px;
    font-family: var(--font-mono, monospace);
    font-size: 0.72rem;
    line-height: 1.5;
  }

  .log-empty {
    color: var(--color-text-muted, #6B7A8D);
    font-style: italic;
  }

  .log-line {
    color: var(--color-text-secondary, #8B9DC3);
    white-space: pre-wrap;
    word-break: break-all;
  }
</style>
