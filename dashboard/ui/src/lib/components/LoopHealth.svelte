<script lang="ts">
  import { onMount, onDestroy } from 'svelte';

  interface LoopStatus {
    name: string;
    alive: boolean;
    last_seen?: string;
  }

  let loops: LoopStatus[] = [];
  let error: string | null = null;
  let loading = true;

  async function fetchLoops() {
    try {
      const res = await fetch('/api/loops/dashboard');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const raw = data.loops || data || {};
      if (Array.isArray(raw)) {
        loops = raw;
      } else if (typeof raw === 'object') {
        loops = Object.entries(raw).map(([name, info]: [string, any]) => ({ name, alive: info.alive, last_seen: info.pid?.toString() }));
      } else {
        loops = [];
      }
      error = null;
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Unknown error';
      error = `Failed to fetch loop health: ${msg}`;
    } finally {
      loading = false;
    }
  }

  let intervalId: ReturnType<typeof setInterval>;

  onMount(() => {
    fetchLoops();
    intervalId = setInterval(fetchLoops, 30_000);
  });

  onDestroy(() => {
    if (intervalId) clearInterval(intervalId);
  });
</script>

<div class="panel">
  <h3 class="section-title">Loop Health</h3>

  {#if loading}
    <p class="empty-state">Loading loop status…</p>
  {:else if error}
    <p class="empty-state" style="color: var(--color-status-fail);">{error}</p>
  {:else if loops.length === 0}
    <p class="empty-state">No loops registered</p>
  {:else}
    <div class="loop-row">
      {#each loops as loop}
        <div class="loop-item">
          <span
            class="loop-dot"
            class:alive={loop.alive}
            class:dead={!loop.alive}
          ></span>
          <span class="loop-name">{loop.name}</span>
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

  .loop-row {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
  }

  .loop-item {
    display: flex;
    gap: 8px;
    align-items: center;
  }

  .loop-dot {
    width: 8px;
    height: 8px;
    border-radius: var(--radius-pill);
    flex-shrink: 0;
  }

  .loop-dot.alive {
    background: var(--color-accent-worker);
    box-shadow: 0 0 6px rgba(89, 227, 138, 0.4);
  }

  .loop-dot.dead {
    background: var(--color-status-fail);
    box-shadow: 0 0 6px rgba(255, 107, 107, 0.4);
  }

  .loop-name {
    font-size: var(--text-body);
    color: var(--color-text-secondary);
    font-family: var(--font-mono);
  }
</style>
