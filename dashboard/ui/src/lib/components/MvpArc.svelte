<script lang="ts">
  import { completionPct } from '$lib/stores/tickets';
  const RADIUS = 34;
  const CIRCUMFERENCE = 2 * Math.PI * RADIUS;
  $: dashOffset = CIRCUMFERENCE - ($completionPct / 100) * CIRCUMFERENCE;
</script>

<div class="mvp-arc">
  <div class="arc-visual">
    <svg viewBox="0 0 80 80" width="80" height="80" class="arc-svg">
      <circle cx="40" cy="40" r="34" fill="none" stroke="var(--color-bg-base)" stroke-width="5" />
      <circle cx="40" cy="40" r="34" fill="none" stroke="var(--color-accent-complete)" stroke-width="5"
        stroke-dasharray={CIRCUMFERENCE} stroke-dashoffset={dashOffset}
        stroke-linecap="round" transform="rotate(-90 40 40)"
        style="transition: stroke-dashoffset 500ms ease-out" />
    </svg>
    <span class="arc-pct">{$completionPct}%</span>
  </div>
  <div class="arc-info">
    <h3 class="arc-title">Swarm Dashboard</h3>
    <span class="arc-stack">SVELTEKIT + FASTAPI</span>
  </div>
</div>

<style>
  .mvp-arc {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .arc-visual {
    position: relative;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }

  .arc-svg {
    display: block;
  }

  .arc-pct {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--color-accent-complete);
    font-family: var(--font-mono);
    pointer-events: none;
  }

  .arc-info {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .arc-title {
    font-size: var(--text-section);
    font-weight: 600;
    color: var(--color-text-primary);
    text-transform: uppercase;
    margin: 0;
    line-height: 1.2;
  }

  .arc-stack {
    font-size: var(--text-badge);
    color: var(--color-text-muted);
    letter-spacing: 0.05em;
    text-transform: uppercase;
  }
</style>
