<script lang="ts">
  import { onMount, onDestroy } from 'svelte';

  interface HardwareData {
    cpu_percent: number | null;
    ram_used_gb: number | null;
    ram_total_gb: number | null;
    gpu_3d_percent: number | null;
    vram_used_gb: number | null;
    npu_percent: number | null;
    temp_c: number | null;
    hostname: string;
    cpu_name: string;
  }

  let data: HardwareData | null = null;
  let loading = true;
  let interval: ReturnType<typeof setInterval> | null = null;

  function fmt(v: number | null, decimals = 0, unit = ''): string {
    if (v === null || v === undefined) return '—';
    return v.toFixed(decimals) + unit;
  }

  function fmtRam(used: number | null, total: number | null): string {
    if (used === null || total === null) return '—';
    return `${used.toFixed(1)} / ${total.toFixed(0)} GB`;
  }

  function tempColor(t: number | null): string {
    if (t === null) return 'var(--color-text-primary, #fff)';
    if (t > 85) return '#ff6b6b';
    if (t > 70) return '#ffd166';
    return '#63d38f';
  }

  async function fetchData() {
    try {
      const res = await fetch('/api/telemetry/hardware-full');
      if (res.ok) data = await res.json();
    } catch { /* keep last */ }
    finally { loading = false; }
  }

  onMount(() => { fetchData(); interval = setInterval(fetchData, 2000); });
  onDestroy(() => { if (interval) clearInterval(interval); });

  $: shortCpu = data?.cpu_name
    ? data.cpu_name.replace(/AMD /i, '').replace(/ w\/.*/, '').trim()
    : 'AMD Ryzen AI';
</script>

<div class="hw-panel">
  <div class="panel-header">
    <span class="panel-title">HARDWARE</span>
    {#if data?.hostname}
      <span class="subtitle-badge">
        <span class="sub-dim">{data.hostname}</span>
        <span class="sub-sep">·</span>
        <span class="sub-name">{shortCpu}</span>
      </span>
    {/if}
  </div>

  {#if loading}
    <div class="loading">Loading…</div>
  {:else if !data}
    <div class="unavailable">Hardware data unavailable</div>
  {:else}
    <div class="stats-grid">
      <div class="stat-block">
        <div class="stat-label">CPU</div>
        <div class="stat-value cpu-color">{fmt(data.cpu_percent, 0, '%')}</div>
      </div>

      <div class="stat-block">
        <div class="stat-label">SYSTEM RAM</div>
        <div class="stat-value ram-color">{fmtRam(data.ram_used_gb, data.ram_total_gb)}</div>
      </div>

      <div class="stat-block">
        <div class="stat-label">GPU</div>
        <div class="stat-value gpu-color">{fmt(data.gpu_3d_percent, 1, '%')}</div>
      </div>

      <div class="stat-block">
        <div class="stat-label">VRAM USED</div>
        <div class="stat-value vram-color">{fmt(data.vram_used_gb, 2, ' GB')}</div>
      </div>

      <div class="stat-block">
        <div class="stat-label">NPU</div>
        <div class="stat-value npu-color">{fmt(data.npu_percent, 1, '%')}</div>
      </div>

      <div class="stat-block" class:hot={data.temp_c !== null && data.temp_c > 70}>
        <div class="stat-label">TEMP</div>
        <div class="stat-value" style="color: {tempColor(data.temp_c)}">{fmt(data.temp_c, 1, '°C')}</div>
      </div>
    </div>
  {/if}
</div>

<style>
  .hw-panel {
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
    flex-wrap: wrap;
  }

  .panel-title {
    font-size: var(--text-section);
    font-weight: 600;
    color: var(--color-text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .subtitle-badge {
    display: flex;
    align-items: center;
    gap: 5px;
    font-size: 11px;
    background: rgba(255,255,255,0.05);
    padding: 2px 8px;
    border-radius: 10px;
  }

  .sub-dim   { color: var(--color-text-muted, rgba(255,255,255,0.35)); }
  .sub-sep   { color: var(--color-text-muted, rgba(255,255,255,0.2)); }
  .sub-name  { color: var(--color-text-secondary, rgba(255,255,255,0.6)); font-weight: 500; }

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

  .stat-block.hot {
    background: rgba(255, 107, 107, 0.07);
    border: 1px solid rgba(255, 107, 107, 0.15);
  }

  .stat-label {
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--color-text-muted, rgba(255,255,255,0.4));
  }

  .stat-value {
    font-size: 18px;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
    line-height: 1.2;
  }

  .cpu-color   { color: #7eb8f7; }
  .ram-color   { color: #c97bdc; font-size: 14px; }
  .gpu-color   { color: #ffd166; }
  .vram-color  { color: #a8dadc; }
  .npu-color   { color: #63d38f; }

  .loading, .unavailable {
    font-size: 13px;
    color: var(--color-text-muted, rgba(255,255,255,0.4));
    padding: 24px 0;
    text-align: center;
  }
</style>
