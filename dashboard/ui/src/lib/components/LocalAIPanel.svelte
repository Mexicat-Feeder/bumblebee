<script lang="ts">
  import { onMount, onDestroy } from 'svelte';

  interface ModelInfo {
    id: string;
    display_name: string;
    recipe: string;
    device: string;
  }

  interface LemonadeData {
    is_live: boolean;
    active_model: string;
    active_model_raw: string;
    all_models: ModelInfo[];
    tokens_per_second: number | null;
    time_to_first_token: number | null;
    input_tokens: number | null;
    output_tokens: number | null;
    npu_utilization: number | null;
    peak_tokens_per_second: number | null;
    peak_npu_utilization: number | null;
    project_start: string | null;
  }

  let data: LemonadeData | null = null;
  let loading = true;
  let interval: ReturnType<typeof setInterval> | null = null;

  function fmtTps(v: number | null): string {
    if (v === null || v === undefined) return '--';
    return v.toFixed(1);
  }

  function fmtTtft(v: number | null): string {
    if (v === null || v === undefined) return '--';
    return v.toFixed(2) + 's';
  }

  function fmtTokens(v: number | null): string {
    if (v === null || v === undefined) return '--';
    if (v >= 1_000_000) return (v / 1_000_000).toFixed(1) + 'M';
    if (v >= 1_000) return (v / 1_000).toFixed(1) + 'k';
    return String(v);
  }

  function modelRole(id: string): string {
    const lower = id.toLowerCase();
    if (lower.includes('gemma') || lower.includes('e4b') || lower.includes('sift')) return 'Sift';
    return 'Forge';
  }

  function modelColor(id: string): string {
    return modelRole(id) === 'Sift' ? '#c97bdc' : '#ffd166';
  }

  async function fetchData() {
    try {
      const res = await fetch('/api/telemetry/lemonade-full');
      if (res.ok) data = await res.json();
    } catch { /* keep last */ }
    finally { loading = false; }
  }

  onMount(() => { fetchData(); interval = setInterval(fetchData, 2000); });
  onDestroy(() => { if (interval) clearInterval(interval); });

  $: models = data?.all_models ?? [];
  $: activeRaw = data?.active_model_raw ?? '';
  $: tps = data?.tokens_per_second;
  $: ttft = data?.time_to_first_token;
  $: inputTok = data?.input_tokens;
  $: outputTok = data?.output_tokens;
</script>

<div class="ai-panel">
  <div class="panel-header">
    <span class="panel-title">LOCAL AI ACTIVITY</span>
    <span class="engine-badge">Lemonade</span>
  </div>

  {#if loading}
    <div class="loading">Loading...</div>
  {:else if !data}
    <div class="unavailable">Lemonade data unavailable</div>
  {:else if models.length === 0}
    <div class="unavailable">No models loaded</div>
  {:else}
    {#each models as model (model.id)}
      {@const isActive = model.id === activeRaw}
      {@const role = modelRole(model.id)}
      {@const color = modelColor(model.id)}
      <div class="model-section" class:active-model={isActive}>
        <div class="model-header">
          <span class="model-role" style="color: {color}">{role}</span>
          <span class="model-name">{model.display_name}</span>
          {#if isActive}
            <span class="active-dot" style="background: {color}" title="Currently generating"></span>
          {/if}
        </div>
        <div class="model-stats">
          <div class="mini-stat" class:highlight={isActive} style="--accent: {color}">
            <span class="mini-label">TOK/S</span>
            <span class="mini-value" style="color: {color}">{isActive ? fmtTps(tps) : '--'}</span>
          </div>
          <div class="mini-stat">
            <span class="mini-label">TTFT</span>
            <span class="mini-value">{isActive ? fmtTtft(ttft) : '--'}</span>
          </div>
          <div class="mini-stat">
            <span class="mini-label">IN</span>
            <span class="mini-value">{isActive ? fmtTokens(inputTok) : '--'}</span>
          </div>
          <div class="mini-stat">
            <span class="mini-label">OUT</span>
            <span class="mini-value">{isActive ? fmtTokens(outputTok) : '--'}</span>
          </div>
        </div>
      </div>
    {/each}
  {/if}
</div>

<style>
  .ai-panel {
    height: 100%;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .panel-title {
    font-size: var(--text-section);
    font-weight: 600;
    color: var(--color-text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .engine-badge {
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    padding: 2px 8px;
    border-radius: 4px;
    background: rgba(89, 227, 138, 0.1);
    color: var(--color-accent-worker, #59e38a);
  }

  .model-section {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    padding: 10px 12px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    transition: border-color 0.3s;
  }

  .model-section.active-model {
    border-color: rgba(255, 255, 255, 0.12);
    background: rgba(255, 255, 255, 0.04);
  }

  .model-header {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .model-role {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }

  .model-name {
    font-size: 13px;
    font-weight: 600;
    color: var(--color-text-primary, #fff);
  }

  .active-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    animation: pulse-dot 2s ease-in-out infinite;
  }

  @keyframes pulse-dot {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
  }

  .model-stats {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr 1fr;
    gap: 6px;
  }

  .mini-stat {
    background: rgba(255, 255, 255, 0.03);
    border-radius: 6px;
    padding: 6px 8px;
    display: flex;
    flex-direction: column;
    gap: 2px;
    text-align: center;
  }

  .mini-stat.highlight {
    background: color-mix(in srgb, var(--accent) 8%, transparent);
    border: 1px solid color-mix(in srgb, var(--accent) 15%, transparent);
  }

  .mini-label {
    font-size: 8px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--color-text-muted, rgba(255,255,255,0.4));
  }

  .mini-value {
    font-size: 15px;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
    color: var(--color-text-primary, #fff);
    line-height: 1.1;
  }

  .loading, .unavailable {
    font-size: 13px;
    color: var(--color-text-muted, rgba(255,255,255,0.4));
    padding: 24px 0;
    text-align: center;
  }
</style>
