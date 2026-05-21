<script lang="ts">
  import { telemetry } from '$lib/stores/telemetry';

  function brightClass(val: number | null): string {
    if (val === null) return '';
    if (val > 90) return 'gauge--critical';
    if (val > 70) return 'gauge--high';
    return '';
  }

  function fmt(val: number | null, suffix: string = ''): string {
    return val !== null ? `${val}${suffix}` : '—';
  }

  function fmtTtft(val: number | null): string {
    return val !== null ? `${val.toFixed(3)}s` : '—';
  }
</script>

<div class="telemetry-panel">
  <!-- Hardware Section -->
  <div class="telemetry-section">
    <h4 class="section-heading">Hardware</h4>

    <div class="gauge-row">
      <span class="gauge-label">CPU</span>
      <span class="gauge-value">{fmt($telemetry.hardware.cpu_percent, '%')}</span>
      <div class="gauge-bar-wrapper {brightClass($telemetry.hardware.cpu_percent)}">
        <div
          class="gauge-bar gauge-bar--cpu"
          style="width: {$telemetry.hardware.cpu_percent ?? 0}%;"
        ></div>
      </div>
    </div>

    <div class="gauge-row">
      <span class="gauge-label">RAM</span>
      <span class="gauge-value">
        {fmt($telemetry.hardware.ram_used_gb, ' / ')}
        {fmt($telemetry.hardware.ram_total_gb, ' GB')}
      </span>
      <div class="gauge-bar-wrapper">
        <div
          class="gauge-bar gauge-bar--ram"
          style="width: {
            $telemetry.hardware.ram_total_gb
              ? ($telemetry.hardware.ram_used_gb / $telemetry.hardware.ram_total_gb) * 100
              : 0
          }%;"
        ></div>
      </div>
    </div>

    <div class="gauge-row">
      <span class="gauge-label">iGPU</span>
      <span class="gauge-value">{fmt($telemetry.hardware.igpu_mem_gb, ' GB')}</span>
      <div class="gauge-bar-wrapper">
        <div
          class="gauge-bar gauge-bar--igpu"
          style="width: {
            $telemetry.hardware.ram_total_gb
              ? ($telemetry.hardware.igpu_mem_gb / $telemetry.hardware.ram_total_gb) * 100
              : 0
          }%;"
        ></div>
      </div>
    </div>

    <div class="gauge-row">
      <span class="gauge-label">GPU 3D</span>
      <span class="gauge-value">{fmt($telemetry.hardware.gpu_3d_percent, '%')}</span>
      <div class="gauge-bar-wrapper {brightClass($telemetry.hardware.gpu_3d_percent)}">
        <div
          class="gauge-bar gauge-bar--gpu"
          style="width: {$telemetry.hardware.gpu_3d_percent ?? 0}%;"
        ></div>
      </div>
    </div>
  </div>

  <!-- Inference Section -->
  <div class="telemetry-section">
    <h4 class="section-heading">Inference</h4>

    <div class="inference-metrics">
      <div class="metric-block">
        <span class="metric-label">TOK/s</span>
        <span
          class="metric-value metric-value--kpi"
          style="color: {
            $telemetry.inference.tokens_per_second && $telemetry.inference.tokens_per_second > 0
              ? 'var(--color-accent-worker)'
              : 'var(--color-text-muted)'
          };"
        >
          {fmt($telemetry.inference.tokens_per_second, '')}
        </span>
      </div>

      <div class="metric-block">
        <span class="metric-label">TTFT</span>
        <span class="metric-value metric-value--ttft">{fmtTtft($telemetry.inference.time_to_first_token)}</span>
      </div>

      <div class="metric-block">
        <span class="metric-label">NPU</span>
        <span class="metric-value">{fmt($telemetry.inference.npu_utilization, '%')}</span>
        <div class="gauge-bar-wrapper {brightClass($telemetry.inference.npu_utilization)}">
          <div
            class="gauge-bar gauge-bar--npu"
            style="width: {$telemetry.inference.npu_utilization ?? 0}%;"
          ></div>
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  @import '../design-tokens.css';

  .telemetry-panel {
    display: flex;
    flex-direction: row;
    gap: 24px;
    width: 100%;
  }

  .telemetry-section {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .section-heading {
    font-size: var(--text-kpi-label);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--color-text-muted);
    margin: 0;
  }

  .gauge-row {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .gauge-label {
    font-size: var(--text-badge);
    font-weight: 500;
    color: var(--color-text-secondary);
    min-width: 52px;
    flex-shrink: 0;
  }

  .gauge-value {
    font-size: var(--text-body);
    font-weight: 600;
    font-family: var(--font-mono);
    color: var(--color-text-primary);
    min-width: 72px;
    text-align: right;
    flex-shrink: 0;
  }

  .gauge-bar-wrapper {
    flex: 1;
    height: 6px;
    border-radius: 3px;
    background: var(--color-bg-base);
    overflow: hidden;
    transition: filter 200ms ease;
  }

  .gauge-bar-wrapper.gauge--high {
    filter: brightness(1.3);
  }

  .gauge-bar-wrapper.gauge--critical {
    filter: brightness(1.6);
  }

  .gauge-bar {
    height: 6px;
    border-radius: 3px;
    transition: width 200ms ease, filter 200ms ease;
  }

  .gauge-bar--cpu {
    background: var(--color-accent-cpu);
  }

  .gauge-bar--ram {
    background: var(--color-accent-primary);
  }

  .gauge-bar--igpu {
    background: var(--color-accent-vram);
  }

  .gauge-bar--gpu {
    background: var(--color-accent-gpu);
  }

  .gauge-bar--npu {
    background: var(--color-accent-npu);
  }

  .inference-metrics {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .metric-block {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .metric-label {
    font-size: var(--text-badge);
    font-weight: 500;
    color: var(--color-text-secondary);
  }

  .metric-value {
    font-size: var(--text-body);
    font-weight: 600;
    font-family: var(--font-mono);
    color: var(--color-text-primary);
    transition: color 200ms ease;
  }

  .metric-value--kpi {
    font-size: var(--text-kpi);
  }

  .metric-value--ttft {
    font-size: var(--text-body);
  }
</style>
