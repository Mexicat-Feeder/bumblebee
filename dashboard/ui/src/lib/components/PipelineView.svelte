<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { pipelineStore } from '$lib/stores/pipeline';
  import { ticketStore } from '$lib/stores/tickets';
  import { openForgeDrawer, openSiftDrawer, openTicketDrawer, openReportDrawer, openCodingDrawer } from '$lib/stores/drawer';
  import { researchStore } from '$lib/stores/research';
  import { projectsStore } from '$lib/stores/projects';
  import type { PipelineState } from '$lib/stores/pipeline';
  import PixelActivity from '$lib/components/PixelActivity.svelte';
  import HardwarePanel from '$lib/components/HardwarePanel.svelte';
  import LocalAIPanel from '$lib/components/LocalAIPanel.svelte';

  export let slug: string = '';
  export let projectName: string = '';
  /** Project status from the projects store */
  export let projectStatus: string = '';

  let state: PipelineState;
  const unsub = pipelineStore.subscribe(s => state = s);

  let costPoller: ReturnType<typeof setInterval> | null = null;
  let cloudCosts: { decompose: number; integration: number; total: number } = { decompose: 0, integration: 0, total: 0 };

  async function fetchCloudCosts() {
    try {
      const res = await fetch('/api/pixel/stats');
      if (res.ok) {
        const d = await res.json();
        if (d.available && d.phases) {
          cloudCosts = {
            decompose: d.phases?.decompose?.cost_usd ?? 0,
            integration: d.phases?.integration?.cost_usd ?? 0,
            total: d.estimatedCostUsd ?? 0,
          };
        }
      }
    } catch { /* ignore */ }
  }

  // Poll cloud costs while pipeline is active
  let cloudCostPoller: ReturnType<typeof setInterval> | null = null;
  $: if (state.phase !== 'idle') {
    if (!cloudCostPoller) {
      fetchCloudCosts();
      cloudCostPoller = setInterval(fetchCloudCosts, 5000);
    }
  } else if (cloudCostPoller) {
    clearInterval(cloudCostPoller);
    cloudCostPoller = null;
  }

  // Auto-detect pipeline phase from project status on load
  let lastAutoSlug = '';
  $: if (slug && slug !== lastAutoSlug) {
    lastAutoSlug = slug;
    if (costPoller) clearInterval(costPoller);
    // If project is already in a build state, start polling
    if (['scaffolded', 'running', 'approved'].includes(projectStatus) && state.phase === 'idle') {
      pipelineStore.startCoding(slug);
    }
  }

  // Sync pipeline store from ticket SSE
  let ticketUnsub: (() => void) | null = null;
  $: if (slug) {
    ticketUnsub?.();
    ticketUnsub = ticketStore.subscribe(ts => {
      if (ts.tickets.length > 0) {
        pipelineStore.updateFromTickets(ts.tickets);
      }
    });
  }

  onDestroy(() => {
    unsub();
    ticketUnsub?.();
    if (costPoller) clearInterval(costPoller);
    if (cloudCostPoller) clearInterval(cloudCostPoller);
  });

  // Show welcome state when no project is selected
  $: noProject = !slug;

  let resetting = false;
  let resetConfirm = false;

  async function doReset() {
    if (!resetConfirm) { resetConfirm = true; return; }
    resetting = true;
    try {
      const resp = await fetch('/api/reset', { method: 'POST' });
      if (resp.ok) {
        pipelineStore.reset();
        await researchStore.fetchTickets();
        await projectsStore.fetchProjects();
      }
    } catch { /* ignore */ }
    resetting = false;
    resetConfirm = false;
  }

  function cancelReset() { resetConfirm = false; }



  // Formatted elapsed time
  $: elapsed = formatTime(state.elapsedSeconds);

  function formatTime(s: number): string {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return m > 0 ? `${m}m ${sec}s` : `${sec}s`;
  }

  // Phase activity states
  $: creatingActive = state.phase === 'creating' || state.phase === 'committing';
  $: codingActive = state.phase === 'coding';
  $: qaActive = state.phase === 'integrating' || state.phase === 'done';

  // Block values
  $: creatingCount = state.createdTickets;
  $: creatingTotal = state.totalTickets;
  $: codingCount = state.codingRemaining;
  $: qaCount = state.qaVerified;
  $: qaFailed = state.qaFailed;

  // Phase completion checks
  $: creatingDone = state.totalTickets > 0 && state.phase !== 'creating' && state.phase !== 'committing';
  $: codingDone = state.phase === 'integrating' || state.phase === 'done';
  $: allDone = state.phase === 'done';

  // Sift research stats
  $: siftTickets = $researchStore.tickets ?? [];
  $: siftQueued = siftTickets.filter((t: any) => t.display_status === 'queued').length;
  $: siftInProgress = siftTickets.filter((t: any) => t.display_status === 'in_progress').length;
  $: siftComplete = siftTickets.filter((t: any) => t.display_status === 'complete').length;
  $: siftTotal = siftTickets.length;
  $: siftSearching = siftInProgress > 0;
</script>

{#if noProject}
<div class="welcome-container">
  <div class="welcome-graphic">
    <svg width="80" height="80" viewBox="0 0 80 80" fill="none">
      <rect x="8" y="20" width="18" height="40" rx="4" fill="rgba(58,190,255,0.15)" stroke="rgba(58,190,255,0.4)" stroke-width="1.5"/>
      <rect x="31" y="12" width="18" height="56" rx="4" fill="rgba(89,227,138,0.15)" stroke="rgba(89,227,138,0.4)" stroke-width="1.5"/>
      <rect x="54" y="24" width="18" height="32" rx="4" fill="rgba(58,190,255,0.15)" stroke="rgba(58,190,255,0.4)" stroke-width="1.5"/>
      <path d="M28 40 L30 40" stroke="rgba(255,255,255,0.3)" stroke-width="1.5"/>
      <path d="M51 40 L53 40" stroke="rgba(255,255,255,0.3)" stroke-width="1.5"/>
    </svg>
  </div>
  <h2 class="welcome-title">Build Pipeline</h2>
  <p class="welcome-sub">Select a project from the sidebar, or create a new one to start building.</p>
</div>
{:else}
<div class="pipeline-container">
  <!-- Header -->
  <div class="pipeline-header">
    <div class="header-left">
      <span class="header-label">BUILD PIPELINE</span>
      <span class="header-project">{projectName}</span>
      {#if resetting}
        <button class="reset-btn" disabled>
          <span class="spinner-inline"></span>
          Resetting...
        </button>
      {:else if resetConfirm}
        <div class="reset-confirm">
          <span class="reset-warn">Clear all tickets & research?</span>
          <button class="reset-yes" on:click={doReset}>Yes, reset</button>
          <button class="reset-no" on:click={cancelReset}>Cancel</button>
        </div>
      {:else}
        <button class="reset-btn" on:click={doReset} title="Reset demo to beginning">
          <svg width="13" height="13" viewBox="0 0 16 16" fill="none">
            <path d="M2 8a6 6 0 1 1 1.5 3.9" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
            <path d="M2 12V8h4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          Reset
        </button>
      {/if}
    </div>
    <div class="header-right">
      {#if state.phase !== 'idle'}
        <span class="elapsed-badge">{elapsed}</span>
      {/if}
      {#if state.error}
        <span class="error-badge">⚠ Error</span>
      {/if}
    </div>
  </div>

  <!-- Forge Row: Creating Tickets → Coding → Integration -->
  <div class="phase-row">
    <!-- Forge Avatar + New Project -->
    <div class="row-avatar">
      <img src="/images/forge-avatar.png" alt="Forge" class="avatar-img" />
      <span class="avatar-name">Forge</span>
      <button class="row-add-btn" on:click={openForgeDrawer} title="New Project">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M8 3v10M3 8h10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
      </button>
    </div>

    <!-- Creating Tickets -->
    <div class="phase-block" class:active={creatingActive} class:done={creatingDone} class:idle={!creatingActive && !creatingDone}>
      <div class="phase-top">
        <span class="phase-badge cloud">☁ Cloud</span>
        {#if state.phase === 'committing'}
          <span class="phase-status pulse">Committing...</span>
        {:else if creatingActive}
          <span class="phase-status pulse">Creating...</span>
        {:else if creatingDone}
          <span class="phase-status check">✓ Done</span>
        {/if}
      </div>
      <h3 class="phase-title">Creating Tickets</h3>
      <div class="phase-metric">
        <span class="metric-big">{creatingCount}</span>
        {#if creatingTotal > 0 && creatingDone}
          <span class="metric-sub">tickets created</span>
        {:else}
          <span class="metric-sub">tickets{creatingActive ? '...' : ''}</span>
        {/if}
      </div>
      {#if cloudCosts.decompose > 0}
        <span class="cost-label">${cloudCosts.decompose.toFixed(3)}</span>
      {/if}
      {#if creatingActive}
        <div class="progress-bar">
          <div class="progress-fill pulse-bar"></div>
        </div>
      {/if}
      {#if creatingActive || creatingDone}
        <button class="details-btn" on:click={openTicketDrawer} title="View ticket details">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M2 4h10M2 7h10M2 10h6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          Details
        </button>
      {/if}
    </div>

    <!-- Arrow -->
    <div class="phase-arrow" class:visible={creatingDone || codingActive}>
      <svg width="32" height="24" viewBox="0 0 32 24">
        <path d="M0 12 L24 12 M18 6 L24 12 L18 18" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </div>

    <!-- Coding -->
    <div class="phase-block" class:active={codingActive} class:done={codingDone} class:idle={!codingActive && !codingDone}>
      <div class="phase-top">
        <span class="phase-badge local">⚡ Local</span>
        {#if codingActive}
          <span class="phase-status pulse">Building...</span>
        {:else if codingDone}
          <span class="phase-status check">✓ Done</span>
        {/if}
      </div>
      <h3 class="phase-title">Coding</h3>
      <div class="phase-metric">
        {#if codingActive || codingDone}
          <span class="metric-big">{qaCount}<span class="metric-dim">/{state.totalTickets}</span></span>
          <span class="metric-sub">verified</span>
        {:else}
          <span class="metric-big">--</span>
          <span class="metric-sub">waiting</span>
        {/if}
      </div>
      <span class="cost-label">$0.00 <span class="cost-note">local</span></span>
      {#if state.codingCurrentId}
        <div class="current-ticket">
          <span class="current-label">Building:</span>
          <span class="current-id">{state.codingCurrentId}</span>
        </div>
      {/if}
      {#if codingActive}
        <div class="progress-bar">
          {#if state.totalTickets > 0}
            <div class="progress-fill" style="width: {Math.round(((state.totalTickets - codingCount) / state.totalTickets) * 100)}%"></div>
          {:else}
            <div class="progress-fill pulse-bar"></div>
          {/if}
        </div>
      {/if}
      {#if codingActive || codingDone}
        <button class="details-btn" on:click={openCodingDrawer} title="View build log">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M2 4h10M2 7h10M2 10h6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          Details
        </button>
      {/if}
    </div>

    <!-- Arrow -->
    <div class="phase-arrow" class:visible={codingDone || qaActive}>
      <svg width="32" height="24" viewBox="0 0 32 24">
        <path d="M0 12 L24 12 M18 6 L24 12 L18 18" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </div>

    <!-- Integration / Wiring -->
    <div class="phase-block" class:active={qaActive && !allDone} class:done={allDone} class:idle={!qaActive}>
      <div class="phase-top">
        <span class="phase-badge cloud">☁ Cloud</span>
        {#if qaActive && !allDone}
          <span class="phase-status pulse">Wiring...</span>
        {:else if allDone}
          <span class="phase-status check">✓ Ready</span>
        {/if}
      </div>
      <h3 class="phase-title">Integration</h3>
      <div class="phase-metric">
        {#if qaActive || codingDone}
          <span class="metric-big">{qaCount}</span>
          <span class="metric-sub">verified</span>
        {:else}
          <span class="metric-big">--</span>
          <span class="metric-sub">waiting</span>
        {/if}
      </div>
      {#if qaFailed > 0}
        <span class="failed-badge">{qaFailed} blocked</span>
      {/if}
      {#if allDone}
        <button class="launch-btn" on:click={() => window.open(`/app/${slug}`, '_blank')}>
          🚀 Launch App
        </button>
      {/if}
    </div>
  </div>

  <!-- Error display -->
  {#if state.error}
    <div class="error-bar">
      <span class="error-icon">⚠</span>
      <span class="error-text">{state.error}</span>
    </div>
  {/if}

  <!-- Sift Row: Searching Internet → Compiling Report -->
  <div class="phase-row sift-row">
    <!-- Sift Avatar + New Research -->
    <div class="row-avatar">
      <img src="/images/sift-avatar.png" alt="Sift" class="avatar-img" />
      <span class="avatar-name">Sift</span>
      <button class="row-add-btn" on:click={openSiftDrawer} title="New Research">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M8 3v10M3 8h10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
      </button>
    </div>

    <!-- Searching Internet -->
    <div class="phase-block" class:active={siftSearching} class:done={siftQueued === 0 && siftComplete > 0 && siftInProgress === 0} class:idle={siftTotal === 0}>
      <div class="phase-top">
        <span class="phase-badge local">⚡ Local</span>
        {#if siftSearching}
          <span class="phase-status pulse">Searching...</span>
        {/if}
      </div>
      <h3 class="phase-title">Searching Internet</h3>
      <div class="phase-metric">
        <span class="metric-big">{siftQueued + siftInProgress}</span>
        <span class="metric-sub">{siftSearching ? 'in queue' : 'queued'}</span>
      </div>
      <span class="cost-label">$0.00</span>
    </div>

    <!-- Arrow -->
    <div class="phase-arrow" class:visible={siftComplete > 0 || siftInProgress > 0}>
      <svg width="32" height="24" viewBox="0 0 32 24">
        <path d="M0 12 L24 12 M18 6 L24 12 L18 18" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </div>

    <!-- Compiling Report -->
    <div class="phase-block" class:active={siftInProgress > 0} class:done={siftComplete > 0 && siftInProgress === 0 && siftQueued === 0} class:idle={siftComplete === 0 && siftInProgress === 0}>
      <div class="phase-top">
        <span class="phase-badge local">⚡ Local</span>
        {#if siftComplete > 0}
          <span class="phase-status check">✓ {siftComplete} done</span>
        {/if}
      </div>
      <h3 class="phase-title">Compiling Report</h3>
      <div class="phase-metric">
        <span class="metric-big">{siftComplete}</span>
        <span class="metric-sub">report{siftComplete !== 1 ? 's' : ''}</span>
      </div>
      <span class="cost-label">$0.00</span>
      {#if siftTotal > 0}
        <button class="details-btn" on:click={openReportDrawer} title="View reports">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M2 4h10M2 7h10M2 10h6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          Details
        </button>
      {/if}
    </div>
  </div>

  <!-- System Panels (Cloud AI Activity | Hardware | Local AI) -->
  <div class="metrics-section">
    <!-- System Panels -->
    <div class="three-col-row">
      <div class="panel">
        <PixelActivity />
      </div>
      <div class="panel">
        <HardwarePanel />
      </div>
      <div class="panel">
        <LocalAIPanel />
      </div>
    </div>
  </div>
</div>
{/if}

<style>
  /* Welcome state */
  .welcome-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 16px;
    min-height: 400px;
    opacity: 0.7;
  }

  .welcome-graphic {
    opacity: 0.6;
  }

  .welcome-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--color-text-primary);
    margin: 0;
  }

  .welcome-sub {
    font-size: 0.85rem;
    color: var(--color-text-muted);
    margin: 0;
    text-align: center;
    max-width: 360px;
  }

  .pipeline-container {
    display: flex;
    flex-direction: column;
    gap: 20px;
    width: 100%;
  }

  /* Header */
  .pipeline-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
  }

  .header-left {
    display: flex;
    flex-direction: column;
    gap: 3px;
  }

  .header-label {
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--color-text-muted);
  }

  .header-project {
    font-size: 1rem;
    font-weight: 600;
    color: var(--color-text-primary);
  }

  .reset-btn {
    display: flex;
    align-items: center;
    gap: 5px;
    padding: 4px 10px;
    background: transparent;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 5px;
    color: var(--color-text-muted);
    font-family: var(--font-ui);
    font-size: 0.65rem;
    cursor: pointer;
    transition: color 0.15s, border-color 0.15s;
  }

  .reset-btn:hover {
    color: #ff6b6b;
    border-color: rgba(255, 107, 107, 0.4);
  }

  .reset-confirm {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .reset-warn {
    font-size: 0.7rem;
    color: #ff6b6b;
  }

  .reset-yes {
    padding: 3px 10px;
    background: rgba(255, 107, 107, 0.15);
    border: 1px solid rgba(255, 107, 107, 0.4);
    border-radius: 4px;
    color: #ff6b6b;
    font-family: var(--font-ui);
    font-size: 0.65rem;
    font-weight: 600;
    cursor: pointer;
  }

  .reset-yes:disabled { opacity: 0.5; cursor: not-allowed; }

  .spinner-inline {
    display: inline-block;
    width: 10px;
    height: 10px;
    border: 1.5px solid rgba(255,80,80,0.3);
    border-top-color: #FF6B6B;
    border-radius: 50%;
    animation: spin-inline 0.6s linear infinite;
    margin-right: 4px;
    vertical-align: middle;
  }

  @keyframes spin-inline {
    to { transform: rotate(360deg); }
  }

  .reset-no {
    padding: 3px 10px;
    background: transparent;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 4px;
    color: var(--color-text-muted);
    font-family: var(--font-ui);
    font-size: 0.65rem;
    cursor: pointer;
  }

  .header-right {
    display: flex;
    gap: 8px;
    align-items: center;
  }

  .elapsed-badge {
    font-size: 0.75rem;
    font-family: var(--font-mono);
    color: var(--color-text-secondary);
    background: rgba(255, 255, 255, 0.06);
    padding: 3px 10px;
    border-radius: var(--radius-pill);
  }

  .error-badge {
    font-size: 0.7rem;
    color: var(--color-alert-blocked);
    background: rgba(255, 107, 107, 0.12);
    padding: 3px 10px;
    border-radius: var(--radius-pill);
  }

  /* Phase row */
  .phase-row {
    display: flex;
    align-items: stretch;
    gap: 8px;
  }

  /* Row avatar */
  .row-avatar {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 8px;
    flex-shrink: 0;
    background: var(--color-bg-panel);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: var(--radius-panel);
    padding: 16px 14px;
    min-width: 80px;
    align-self: stretch;
  }

  .avatar-img {
    width: 52px;
    height: 52px;
    border-radius: 10px;
    object-fit: cover;
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  }

  .avatar-name {
    font-size: 0.65rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--color-text-muted);
  }

  .row-add-btn {
    width: 28px;
    height: 28px;
    border-radius: 6px;
    border: 1px solid rgba(255, 255, 255, 0.15);
    background: transparent;
    color: var(--color-text-muted);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: color 0.15s, border-color 0.15s, background-color 0.15s;
    margin-top: auto;
  }

  .row-add-btn:hover {
    color: var(--color-accent-primary);
    border-color: rgba(58, 190, 255, 0.4);
    background: rgba(58, 190, 255, 0.08);
  }

  .sift-row {
    margin-top: 4px;
  }

  .phase-arrow {
    display: flex;
    align-items: center;
    padding: 0;
    color: var(--color-text-muted);
    opacity: 0.2;
    transition: opacity 0.4s ease;
    flex-shrink: 0;
  }

  .phase-arrow.visible {
    opacity: 0.7;
    color: var(--color-accent-primary);
  }

  /* Phase block */
  .phase-block {
    flex: 1;
    background: var(--color-bg-panel);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: var(--radius-panel);
    padding: 20px 24px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    transition: border-color 0.3s ease, box-shadow 0.3s ease;
    min-width: 0;
  }

  .phase-block.idle {
    opacity: 0.4;
  }

  .phase-block.active {
    border-color: rgba(58, 190, 255, 0.4);
    box-shadow: 0 0 20px rgba(58, 190, 255, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.04);
    opacity: 1;
  }

  .phase-block.done {
    border-color: rgba(89, 227, 138, 0.3);
    box-shadow: 0 0 12px rgba(89, 227, 138, 0.06);
    opacity: 1;
  }

  /* Phase top row */
  .phase-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .phase-badge {
    font-size: 0.6rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    padding: 2px 8px;
    border-radius: var(--radius-pill);
  }

  .phase-badge.cloud {
    background: rgba(58, 190, 255, 0.12);
    color: var(--color-accent-primary);
  }

  .phase-badge.local {
    background: rgba(89, 227, 138, 0.12);
    color: var(--color-accent-worker);
  }

  .phase-status {
    font-size: 0.65rem;
    font-weight: 600;
    color: var(--color-text-muted);
  }

  .phase-status.pulse {
    color: var(--color-accent-primary);
    animation: statusPulse 2s ease-in-out infinite;
  }

  .phase-status.check {
    color: var(--color-accent-worker);
  }

  @keyframes statusPulse {
    0%, 100% { opacity: 0.6; }
    50% { opacity: 1; }
  }

  .phase-title {
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--color-text-primary);
    margin: 0;
  }

  /* Phase metric */
  .phase-metric {
    display: flex;
    align-items: baseline;
    gap: 8px;
  }

  .metric-big {
    font-size: 2.2rem;
    font-weight: 700;
    font-family: var(--font-mono);
    color: var(--color-text-primary);
    line-height: 1;
  }

  .metric-sub {
    font-size: 0.75rem;
    color: var(--color-text-muted);
  }

  .metric-dim {
    font-size: 0.65em;
    color: var(--color-text-muted);
    font-weight: 400;
  }

  .cost-label {
    font-size: 0.7rem;
    font-family: var(--font-mono);
    color: var(--color-text-muted);
  }

  /* Current ticket indicator */
  .current-ticket {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.7rem;
    margin-top: 2px;
  }

  .current-label {
    color: var(--color-text-muted);
  }

  .current-id {
    font-family: var(--font-mono);
    color: var(--color-accent-primary);
    font-weight: 600;
  }

  /* Progress bar */
  .progress-bar {
    width: 100%;
    height: 3px;
    background: rgba(255, 255, 255, 0.06);
    border-radius: 2px;
    overflow: hidden;
    margin-top: auto;
  }

  .progress-fill {
    height: 100%;
    background: var(--color-accent-primary);
    border-radius: 2px;
    transition: width 0.5s ease;
  }

  .pulse-bar {
    width: 100%;
    background: linear-gradient(90deg, transparent, var(--color-accent-primary), transparent);
    animation: progressPulse 2s ease-in-out infinite;
  }

  @keyframes progressPulse {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
  }

  /* Details button */
  .details-btn {
    display: flex;
    align-items: center;
    gap: 5px;
    padding: 6px 12px;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 6px;
    color: var(--color-text-secondary);
    font-family: var(--font-ui);
    font-size: 0.7rem;
    font-weight: 500;
    cursor: pointer;
    transition: color 0.15s, border-color 0.15s, background-color 0.15s;
    margin-top: auto;
    width: fit-content;
  }

  .details-btn:hover {
    color: var(--color-accent-primary);
    border-color: rgba(58, 190, 255, 0.4);
    background: rgba(58, 190, 255, 0.08);
  }

  /* Failed badge */
  .failed-badge {
    font-size: 0.65rem;
    font-weight: 600;
    color: var(--color-alert-blocked);
    background: rgba(255, 107, 107, 0.12);
    padding: 2px 8px;
    border-radius: var(--radius-pill);
    width: fit-content;
  }

  /* Launch button */
  .launch-btn {
    margin-top: 8px;
    padding: 10px 20px;
    background: linear-gradient(135deg, var(--color-accent-worker), #2BC5A5);
    border: none;
    border-radius: 8px;
    color: #0B1220;
    font-family: var(--font-ui);
    font-size: 0.85rem;
    font-weight: 700;
    cursor: pointer;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
  }

  .launch-btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(89, 227, 138, 0.3);
  }

  /* Error bar */
  .error-bar {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 16px;
    background: rgba(255, 107, 107, 0.08);
    border: 1px solid rgba(255, 107, 107, 0.2);
    border-radius: 8px;
    font-size: 0.8rem;
    color: var(--color-alert-blocked);
  }

  .error-icon { font-size: 1rem; }



  /* System panels row */
  .metrics-section {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .three-col-row {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: var(--spacing-row-gap);
  }

  .panel {
    background: var(--color-bg-panel);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: var(--radius-panel);
    box-shadow: 0 4px 32px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.04);
    padding: var(--spacing-panel-pad);
    min-height: 200px;
  }

  /* Responsive */
  @media (max-width: 900px) {
    .phase-row {
      flex-direction: column;
      gap: 12px;
    }
    .phase-arrow {
      transform: rotate(90deg);
      padding: 4px 0;
      justify-content: center;
    }
    .three-col-row {
      grid-template-columns: 1fr 1fr;
    }
  }
</style>
