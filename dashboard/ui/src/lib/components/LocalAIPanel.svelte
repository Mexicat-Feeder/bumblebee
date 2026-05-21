<script lang="ts">
  import { onMount, onDestroy } from 'svelte';

  interface LemonadeData {
    is_live: boolean;
    active_model: string;
    active_model_raw: string;
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
    if (v === null || v === undefined) return '—';
    return v.toFixed(1);
  }

  function fmtTtft(v: number | null): string {
    if (v === null || v === undefined) return '—';
    return v.toFixed(2) + 's';
  }

  function fmtTokens(v: number | null): string {
    if (v === null || v === undefined) return '—';
    if (v >= 1_000_000) return (v / 1_000_000).toFixed(1) + 'M';
    if (v >= 1_000) return (v / 1_000).toFixed(1) + 'k';
    return String(v);
  }

  function fmtSince(iso: string | null): string {
    if (!iso) return '';
    const d = new Date(iso);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
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

  $: offline = data !== null && !data?.is_live;
  $: tps = data?.is_live ? data.tokens_per_second : data?.peak_tokens_per_second;
</script>

<div class="ai-panel">
  <div class="panel-header">
    <span class="panel-title">LOCAL AI ACTIVITY</span>
    {#if data?.project_start}
      <span class="since-badge">since {fmtSince(data.project_start)}</span>
    {/if}
  </div>

  <div class="model-row">
    <span class="model-provider">Lemonade</span>
    <span class="model-name">{data?.active_model ?? 'Qwen3.6 35B'}</span>
    {#if data && !data.is_live}
      <span class="offline-dot" title="Lemonade offline — showing peak values">●</span>
    {/if}
  </div>

  {#if loading}
    <div class="loading">Loading…</div>
  {:else if !data}
    <div class="unavailable">Lemonade data unavailable</div>
  {:else}
    <div class="stats-grid">
      <div class="stat-block highlight-tps">
        <div class="stat-label-row">
          <span class="stat-label">TOK/S</span>
          {#if offline}<span class="peak-badge">peak</span>{/if}
        </div>
        <div class="stat-value tps-color">{fmtTps(tps)}</div>
      </div>

      <div class="stat-block">
        <div class="stat-label-row">
          <span class="stat-label">TTFT</span>
          {#if offline}<span class="last-badge">last</span>{/if}
        </div>
        <div class="stat-value ttft-color">{fmtTtft(data.time_to_first_token)}</div>
      </div>

      <div class="stat-block">
        <div class="stat-label-row">
          <span class="stat-label">INPUT TOKENS</span>
          {#if offline}<span class="last-badge">last</span>{/if}
        </div>
        <div class="stat-value in-color">{fmtTokens(data.input_tokens)}</div>
      </div>

      <div class="stat-block">
        <div class="stat-label-row">
          <span class="stat-label">OUTPUT TOKENS</span>
          {#if offline}<span class="last-badge">last</span>{/if}
        </div>
        <div class="stat-value out-color">{fmtTokens(data.output_tokens)}</div>
      </div>
    </div>
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
    gap: 8px;
    flex-wrap: wrap;
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
    margin-top: -4px;
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

  .offline-dot {
    color: #ff6b6b;
    font-size: 8px;
    line-height: 1;
  }

  .stats-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    flex: 1;
  }

  .stat-block {
    background: rgba(255,255,255,0.04);
    border-radius: 8px;
    padding: 10px 12px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .stat-block.highlight-tps {
    background: rgba(255, 209, 102, 0.07);
    border: 1px solid rgba(255, 209, 102, 0.15);
  }

  .stat-label-row {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .stat-label {
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--color-text-muted, rgba(255,255,255,0.4));
  }

  .peak-badge {
    font-size: 9px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: rgba(255, 209, 102, 0.7);
    background: rgba(255, 209, 102, 0.1);
    padding: 1px 5px;
    border-radius: 4px;
  }

  .last-badge {
    font-size: 9px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: rgba(107, 122, 141, 0.8);
    background: rgba(107, 122, 141, 0.12);
    padding: 1px 5px;
    border-radius: 4px;
  }

  .stat-value {
    font-size: 22px;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
    line-height: 1.1;
  }

  .tps-color  { color: #ffd166; }
  .ttft-color { color: #a8dadc; }
  .in-color   { color: #7eb8f7; }
  .out-color  { color: #c97bdc; }

  .loading, .unavailable {
    font-size: 13px;
    color: var(--color-text-muted, rgba(255,255,255,0.4));
    padding: 24px 0;
    text-align: center;
  }
</style>
