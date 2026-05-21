<script lang="ts">
  import { onMount } from 'svelte';
  import { totalScope, completionPct, blockedCount, blockedTickets, activeTicket } from '$lib/stores/tickets';

  export let projectName = 'Swarm Operations Dashboard';
  let loadingProject = true;
  let healthLights: { name: string; ok: boolean }[] = [];

  async function fetchHealth() {
    try {
      const res = await fetch('/api/swarm/health');
      if (res.ok) {
        const data = await res.json();
        healthLights = data.lights ?? [];
      }
    } catch { /* keep last */ }
  }

  async function fetchProject() {
    // Use prop if set, otherwise try API
    if (projectName !== 'Swarm Operations Dashboard') {
      loadingProject = false;
      return;
    }
    try {
      const res = await fetch('/api/projects');
      if (res.ok) {
        const data = await res.json();
        const projects = data.projects ?? data ?? [];
        const active = projects.find((p: any) => p.active) ?? projects[0];
        if (active?.display_name) projectName = active.display_name;
        else if (active?.slug) projectName = active.slug;
      }
    } catch { /* keep default */ }
    finally { loadingProject = false; }
  }

  onMount(() => {
    fetchProject();
    fetchHealth();
    const interval = setInterval(fetchHealth, 15000);
    return () => clearInterval(interval);
  });
</script>

<section class="kpi-section">

  <!-- Title bar -->
  <div class="title-bar">
    <div class="title-stack">
      <span class="main-title">AGENT SWARM DASHBOARD</span>
      <span class="sub-title">{projectName}</span>
    </div>
    <div class="health-lights">
      {#each healthLights as light}
        <div class="health-light" class:light-ok={light.ok} class:light-fail={!light.ok} title={light.name}>
          <span class="light-dot"></span>
          <span class="light-label">{light.name}</span>
        </div>
      {/each}
    </div>
  </div>

  <!-- 4 tinted metric squares -->
  <div class="metric-row">

    <div class="metric-square sq-cyan">
      <span class="metric-label">TOTAL TICKETS</span>
      <span class="metric-value">{$totalScope}</span>
    </div>

    <div class="metric-square sq-teal">
      <span class="metric-label">COMPLETE</span>
      <span class="metric-value">{$completionPct}%</span>
    </div>

    <div class="metric-square" class:sq-alert={$blockedCount > 0} class:sq-muted={$blockedCount === 0}>
      <span class="metric-label">BLOCKED</span>
      <span class="metric-value">{$blockedCount}</span>
      {#if $blockedCount > 0}
        <div class="blocked-list">
          {#each $blockedTickets as t}
            <span class="blocked-id">{t.id}</span>
          {/each}
        </div>
      {/if}
    </div>

    <div class="metric-square" class:sq-green={$activeTicket?.status === 'in_progress'} class:sq-muted={$activeTicket?.status !== 'in_progress'}>
      <span class="metric-label">ACTIVE TICKET</span>
      <span class="ticket-id">{$activeTicket?.id ?? '—'}</span>
      {#if $activeTicket}
        <span class="ticket-status">{$activeTicket.status}</span>
      {/if}
    </div>

  </div>
</section>

<style>
  .kpi-section {
    background: var(--color-bg-panel-raised);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: var(--radius-panel);
    box-shadow: 0 4px 32px rgba(0, 0, 0, 0.5);
    overflow: hidden;
    width: 100%;
    min-width: 0;
    padding: 16px 20px;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  /* Title bar */
  .title-bar {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
  }

  .title-stack {
    display: flex;
    flex-direction: column;
    gap: 3px;
  }

  .main-title {
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--color-text-muted);
  }

  .sub-title {
    font-size: 1rem;
    font-weight: 600;
    color: var(--color-text-primary);
    letter-spacing: 0.01em;
  }

  .health-lights {
    display: flex;
    align-items: center;
    gap: 12px;
    align-self: flex-start;
    padding-top: 2px;
  }

  .health-light {
    display: flex;
    align-items: center;
    gap: 5px;
  }

  .light-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
    background: var(--color-text-muted);
  }

  .light-label {
    font-size: 0.62rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--color-text-muted);
  }

  .health-light.light-ok .light-dot {
    background: var(--color-status-pass);
    box-shadow: 0 0 6px var(--color-status-pass);
  }

  .health-light.light-ok .light-label {
    color: var(--color-text-muted);
  }

  .health-light.light-fail .light-dot {
    background: var(--color-status-fail);
    box-shadow: 0 0 6px var(--color-status-fail);
  }

  .health-light.light-fail .light-label {
    color: var(--color-status-fail);
  }

  /* Metric squares row */
  .metric-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    min-width: 0;
  }

  /* Base tinted square — matches Row 3 stat blocks */
  .metric-square {
    border-radius: 8px;
    padding: 12px 14px;
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 0;
    overflow: hidden;
  }

  /* Colour variants */
  .sq-cyan {
    background: rgba(58, 190, 255, 0.14);
    border: 1px solid rgba(58, 190, 255, 0.30);
  }

  .sq-teal {
    background: rgba(45, 230, 230, 0.14);
    border: 1px solid rgba(45, 230, 230, 0.30);
  }

  .sq-green {
    background: rgba(89, 227, 138, 0.14);
    border: 1px solid rgba(89, 227, 138, 0.30);
  }

  .sq-alert {
    background: rgba(255, 107, 107, 0.14);
    border: 1px solid rgba(255, 107, 107, 0.30);
  }

  .sq-muted {
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.12);
  }

  /* Label */
  .metric-label {
    font-size: 0.62rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--color-text-muted);
  }

  /* Main numeric value */
  .metric-value {
    font-size: 2rem;
    font-weight: 700;
    font-family: var(--font-mono);
    color: var(--color-text-primary);
    line-height: 1.1;
  }

  /* Active ticket ID — small, monospace, no overflow */
  .ticket-id {
    font-size: 0.8rem;
    font-weight: 600;
    font-family: var(--font-mono);
    color: var(--color-text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .ticket-status {
    font-size: 0.62rem;
    color: var(--color-text-muted);
    text-transform: capitalize;
  }

  /* Blocked ticket ID pills */
  .blocked-list {
    display: flex;
    flex-wrap: wrap;
    gap: 3px;
    margin-top: 2px;
  }

  .blocked-id {
    font-size: 0.58rem;
    font-family: var(--font-mono);
    color: var(--color-alert-blocked);
    background: rgba(255, 107, 107, 0.12);
    padding: 1px 5px;
    border-radius: 3px;
    white-space: nowrap;
  }
</style>

