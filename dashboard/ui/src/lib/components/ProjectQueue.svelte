<script lang="ts">
  import { onMount } from 'svelte';
  let projects: Array<{slug: string; active?: boolean}> = [];
  let error = false;
  onMount(async () => {
    try {
      const resp = await fetch('/api/projects');
      const data = await resp.json();
      projects = data.projects || [];
    } catch {
      error = true;
    }
  });
  $: active = projects.find(p => p.active);
  $: onDeck = projects.filter(p => !p.active);
</script>

<div class="project-queue">
  <div class="section-label">PROJECTS</div>
  {#if error}
    <span class="muted">—</span>
  {:else if projects.length === 0}
    <span class="muted">No projects found</span>
  {:else}
    <div class="active-line">
      <span class="dot"></span>
      <span class="active-name">{active?.slug ?? '—'}</span>
      <span class="badge">ACTIVE</span>
    </div>
    {#if onDeck.length > 0}
      <span class="on-deck">On-deck: {onDeck.map(p => p.slug).join(', ')}</span>
    {/if}
  {/if}
</div>

<style>
  .project-queue {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .section-label {
    font-size: var(--text-badge);
    font-weight: 600;
    color: var(--color-text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .muted {
    color: var(--color-text-muted);
    font-size: var(--text-body);
  }

  .active-line {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: var(--text-body);
    color: var(--color-text-primary);
  }

  .dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--color-accent-complete);
    flex-shrink: 0;
  }

  .active-name {
    font-weight: 600;
  }

  .badge {
    font-size: var(--text-badge);
    font-weight: 600;
    color: var(--color-accent-complete);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    background: var(--color-bg-elevated);
    padding: 1px 6px;
    border-radius: 4px;
  }

  .on-deck {
    font-size: var(--text-body);
    color: var(--color-text-muted);
  }
</style>
