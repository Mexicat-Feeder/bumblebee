<script lang="ts">
  import { onMount } from 'svelte';
  import KpiBoard from '$lib/components/KpiBoard.svelte';
  import GateProgress from '$lib/components/GateProgress.svelte';
  import MvpArc from '$lib/components/MvpArc.svelte';
  import TelemetryPanel from '$lib/components/TelemetryPanel.svelte';

  const PANELS = ['kpi', 'gates', 'arc', 'telemetry'] as const;
  const CYCLE_MS = 8000;
  let currentIndex = 0;
  let visible = true;
  let interval: ReturnType<typeof setInterval>;

  function cycle() {
    visible = false;
    setTimeout(() => {
      currentIndex = (currentIndex + 1) % PANELS.length;
      visible = true;
    }, 300);
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') window.location.href = '/';
  }

  onMount(() => {
    interval = setInterval(cycle, CYCLE_MS);
    window.addEventListener('keydown', handleKeydown);
    return () => { clearInterval(interval); window.removeEventListener('keydown', handleKeydown); };
  });
</script>

<div class="presentation" class:visible>
  {#if PANELS[currentIndex] === 'kpi'}
    <KpiBoard />
  {:else if PANELS[currentIndex] === 'gates'}
    <GateProgress />
  {:else if PANELS[currentIndex] === 'arc'}
    <MvpArc />
  {:else if PANELS[currentIndex] === 'telemetry'}
    <TelemetryPanel />
  {/if}
</div>

<style>
  .presentation {
    width: 100vw;
    height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--color-bg-base);
    padding: 40px;
    opacity: 1;
    transition: opacity 300ms ease;
    font-size: 120%;
  }
  .presentation:not(.visible) { opacity: 0; }
</style>
