<script lang="ts">
  import { onMount, onDestroy } from 'svelte';

  interface PixelStats {
    available: boolean;
    model?: string;
    modelRaw?: string;
    provider?: string;
    inputTokens?: number;
    outputTokens?: number;
    cacheRead?: number;
    cacheWrite?: number;
    totalTokens?: number;
    contextTokens?: number;
    estimatedCostUsd?: number;
    sessionStartedAt?: number;
    projectStart?: string;
  }

  let stats: PixelStats = { available: false };
  let loading = true;
  let interval: ReturnType<typeof setInterval> | null = null;

  function formatCost(usd: number): string {
    if (usd >= 1) return '$' + usd.toFixed(2);
    if (usd >= 0.01) return '$' + usd.toFixed(3);
    return '$' + usd.toFixed(4);
  }

  function formatTokens(n: number): string {
    if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
    if (n >= 1_000) return (n / 1_000).toFixed(1) + 'k';
    return String(n);
  }

  function formatSince(ts: number | undefined, projectStart: string | undefined): string {
    const ref = projectStart ? new Date(projectStart).getTime() : ts;
    if (!ref) return '—';
    const d = new Date(ref);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  }

  function cleanModelName(raw: string | undefined): string {
    if (!raw) return '—';
    return raw.replace(/(\d+) (\d+)$/, '$1.$2');
  }

  function providerLabel(p: string | undefined): string {
    if (!p) return '';
    if (p === 'anthropic') return 'Anthropic';
    if (p === 'openai') return 'OpenAI';
    return p.charAt(0).toUpperCase() + p.slice(1);
  }

  async function fetchStats() {
    try {
      const res = await fetch('/api/pixel/stats');
      if (res.ok) stats = await res.json();
    } catch { /* keep last */ }
    finally { loading = false; }
  }

  // Fetch local AI token counts for cost savings calculation
  let localInputTokens = 0;
  let localOutputTokens = 0;

  async function fetchLocalTokens() {
    try {
      const res = await fetch('/api/telemetry/lemonade-full');
      if (res.ok) {
        const d = await res.json();
        localInputTokens = d.input_tokens ?? 0;
        localOutputTokens = d.output_tokens ?? 0;
      }
    } catch { /* keep last */ }
  }

  onMount(() => {
    fetchStats();
    fetchLocalTokens();
    interval = setInterval(() => { fetchStats(); fetchLocalTokens(); }, 15000);
  });
  onDestroy(() => { if (interval) clearInterval(interval); });

  // Cloud cost savings: what local tokens would have cost on Claude Opus
  // Claude Opus 4: $15/M input, $75/M output
  $: savedUsd = (localInputTokens / 1_000_000) * 15 + (localOutputTokens / 1_000_000) * 75;

  $: totalInput = (stats.cacheRead ?? 0) + (stats.inputTokens ?? 0);
  $: contextLimit = stats.contextTokens ?? 1_000_000;

  $: contextPct = contextLimit > 0
    ? Math.round((totalInput / contextLimit) * 100)
    : 0;

  $: contextLabel = formatTokens(totalInput) + ' / ' + formatTokens(contextLimit);
</script>

<div class="pixel-panel">
  <div class="panel-header">
    <span class="panel-title">CLOUD AI ACTIVITY</span>
    {#if stats.available}
      <span class="since-badge">since {formatSince(stats.sessionStartedAt, stats.projectStart ?? undefined)}</span>
    {/if}
  </div>

  {#if loading}
    <div class="loading">Loading…</div>
  {:else if !stats.available}
    <div class="unavailable">Session data unavailable</div>
  {:else}
    <div class="model-row">
      <span class="model-provider">{providerLabel(stats.provider)}</span>
      <span class="model-name">{cleanModelName(stats.model)}</span>
    </div>

    <div class="stats-grid">
      <div class="stat-block highlight-cost">
        <div class="stat-label">EST. COST</div>
        <div class="stat-value cost-color">{formatCost(stats.estimatedCostUsd ?? 0)}</div>
        <div class="stat-sub">this session</div>
      </div>

      <div class="stat-block highlight-cache">
        <div class="stat-label">LOCAL SAVINGS</div>
        <div class="stat-value cache-color">{formatCost(savedUsd)}</div>
        <div class="stat-sub">vs cloud for local work</div>
      </div>

      <div class="stat-block">
        <div class="stat-label">OUTPUT</div>
        <div class="stat-value output-color">{formatTokens(stats.outputTokens ?? 0)}</div>
        <div class="stat-sub">tokens generated</div>
      </div>

      <div class="stat-block">
        <div class="stat-label">CONTEXT USED</div>
        <div class="stat-value context-color">{contextPct}%</div>
        <div class="stat-sub">{contextLabel}</div>
      </div>
    </div>
  {/if}
</div>

<style>
  .pixel-panel {
    height: 100%;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }

  .panel-title {
    font-size: var(--text-section);
    font-weight: 600;
    color: var(--color-text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .since-badge {
    font-size: 11px;
    color: var(--color-text-muted, rgba(255,255,255,0.35));
    background: rgba(255,255,255,0.05);
    padding: 2px 8px;
    border-radius: 10px;
  }

  .model-row {
    display: flex;
    align-items: baseline;
    gap: 8px;
  }

  .model-provider {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--color-text-muted, rgba(255,255,255,0.4));
  }

  .model-name {
    font-size: 15px;
    font-weight: 600;
    color: var(--color-text-primary, #fff);
  }

  .stats-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    flex: 1;
  }

  .stat-block {
    background: rgba(255,255,255,0.04);
    border-radius: 8px;
    padding: 12px 14px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .stat-block.highlight-cost {
    background: rgba(99, 211, 143, 0.07);
    border: 1px solid rgba(99, 211, 143, 0.15);
  }

  .stat-block.highlight-cache {
    background: rgba(126, 184, 247, 0.07);
    border: 1px solid rgba(126, 184, 247, 0.15);
  }

  .stat-label {
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--color-text-muted, rgba(255,255,255,0.4));
  }

  .stat-value {
    font-size: 22px;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
    line-height: 1.1;
  }

  .stat-sub {
    font-size: 10px;
    color: var(--color-text-muted, rgba(255,255,255,0.35));
  }

  .cost-color    { color: #63d38f; }
  .cache-color   { color: #7eb8f7; }
  .output-color  { color: #c97bdc; }
  .context-color { color: #ffd166; }

  .loading, .unavailable {
    font-size: 13px;
    color: var(--color-text-muted, rgba(255,255,255,0.4));
    padding: 24px 0;
    text-align: center;
  }
</style>
