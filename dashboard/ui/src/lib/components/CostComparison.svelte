<script lang="ts">
  import { onMount, onDestroy } from 'svelte';

  // ─── Types ────────────────────────────────────────────────────────────────
  interface CloudCosts {
    claude_opus: number;
    gpt4o: number;
  }

  interface CostData {
    project_name: string;
    total_tickets: number;
    total_duration_s: number;
    total_tool_calls: number;
    total_files_written: number;
    estimated_input_tokens: number;
    estimated_output_tokens: number;
    cloud_costs: CloudCosts;
    local_cost: number; // always 0
  }

  // ─── Props ────────────────────────────────────────────────────────────────
  export let slug: string = '';

  // ─── State ────────────────────────────────────────────────────────────────
  let data: CostData | null = null;
  let loading = true;
  let error: string | null = null;
  let pricingOpen = false;
  let interval: ReturnType<typeof setInterval> | null = null;

  // ─── Token estimation constants (based on real Forge dispatch data) ───────
  //   • ~3,000 input tokens  per tool call  (prompt + rolling context window)
  //   • ~1,500 output tokens per tool call  (code generation + JSON responses)
  const INPUT_TOKENS_PER_CALL  = 3_000;
  const OUTPUT_TOKENS_PER_CALL = 1_500;

  // ─── Cloud pricing (as of 2026, per million tokens) ──────────────────────
  const CLAUDE_OPUS_INPUT_PER_M  = 15.00;
  const CLAUDE_OPUS_OUTPUT_PER_M = 75.00;
  const GPT4O_INPUT_PER_M        =  2.50;
  const GPT4O_OUTPUT_PER_M       = 10.00;

  // ─── Formatters ──────────────────────────────────────────────────────────
  function fmtDollars(v: number): string {
    return '$' + v.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  function fmtTokens(v: number): string {
    if (v >= 1_000_000) return (v / 1_000_000).toFixed(1) + 'M';
    if (v >= 1_000)     return (v / 1_000).toFixed(1) + 'k';
    return String(v);
  }

  function fmtDuration(secs: number): string {
    if (!secs) return '0m';
    const h = Math.floor(secs / 3600);
    const m = Math.floor((secs % 3600) / 60);
    if (h > 0) return `${h}h ${m}m`;
    return `${m}m`;
  }

  function fmtSavingsPct(saved: number, cloudCost: number): string {
    if (cloudCost <= 0) return '0%';
    return Math.round((saved / cloudCost) * 100) + '%';
  }

  // ─── Derived values (reactive) ───────────────────────────────────────────
  $: claudeSaved  = data ? data.cloud_costs.claude_opus - data.local_cost : 0;
  $: gpt4oSaved   = data ? data.cloud_costs.gpt4o       - data.local_cost : 0;
  $: maxCloudCost = data ? Math.max(data.cloud_costs.claude_opus, data.cloud_costs.gpt4o) : 0;
  $: totalSaved   = claudeSaved; // use Claude Opus as headline (higher / more dramatic)

  // ─── Data fetching ───────────────────────────────────────────────────────
  async function fetchData() {
    if (!slug) return;
    try {
      const res = await fetch(`/api/costs/${slug}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      data  = await res.json();
      error = null;
    } catch (e: any) {
      error = e?.message ?? 'Failed to load cost data';
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    fetchData();
    interval = setInterval(fetchData, 30_000);
  });

  onDestroy(() => {
    if (interval) clearInterval(interval);
  });
</script>

<!-- ═══════════════════════════════════════════════════════════════════════════
     TEMPLATE
════════════════════════════════════════════════════════════════════════════ -->
<div class="cost-panel">

  <!-- Header -->
  <div class="panel-header">
    <div class="header-left">
      <span class="panel-title">COST COMPARISON</span>
      <span class="panel-subtitle">Cloud API vs Local AI</span>
    </div>
    {#if data?.project_name}
      <span class="project-badge">{data.project_name}</span>
    {/if}
  </div>

  {#if loading}
    <div class="state-msg">Loading…</div>

  {:else if error}
    <div class="state-msg error">{error}</div>

  {:else if data}

    <!-- ── Cost Cards ────────────────────────────────────────────────────── -->
    <div class="cards-row">

      <!-- Claude Opus 4 -->
      <div class="cost-card cloud-card">
        <div class="card-provider">Anthropic</div>
        <div class="card-model">Claude Opus 4</div>
        <div class="card-cost cloud-cost">{fmtDollars(data.cloud_costs.claude_opus)}</div>
        <div class="card-tokens">
          <span class="token-line">↑ {fmtTokens(data.estimated_input_tokens)} in</span>
          <span class="token-line">↓ {fmtTokens(data.estimated_output_tokens)} out</span>
        </div>
      </div>

      <!-- GPT-4o -->
      <div class="cost-card cloud-card">
        <div class="card-provider">OpenAI</div>
        <div class="card-model">GPT-4o</div>
        <div class="card-cost cloud-cost">{fmtDollars(data.cloud_costs.gpt4o)}</div>
        <div class="card-tokens">
          <span class="token-line">↑ {fmtTokens(data.estimated_input_tokens)} in</span>
          <span class="token-line">↓ {fmtTokens(data.estimated_output_tokens)} out</span>
        </div>
      </div>

      <!-- Local / Lemonade -->
      <div class="cost-card local-card">
        <div class="card-provider">Local</div>
        <div class="card-model">Lemonade</div>
        <div class="card-cost local-cost">$0.00</div>
        <div class="free-badge">FREE</div>
      </div>

    </div>

    <!-- ── Savings Bar ────────────────────────────────────────────────────── -->
    <div class="savings-bar">
      <span class="savings-label">You saved</span>
      <span class="savings-amount">{fmtDollars(totalSaved)}</span>
      <span class="savings-pct">({fmtSavingsPct(totalSaved, data.cloud_costs.claude_opus)})</span>
      <span class="savings-vs">vs Claude Opus 4</span>
    </div>

    <!-- ── Project Stats ──────────────────────────────────────────────────── -->
    <div class="stats-section">
      <div class="stats-title">PROJECT STATS</div>
      <div class="stats-grid">

        <div class="stat-block">
          <div class="stat-label">TICKETS</div>
          <div class="stat-value neutral">{data.total_tickets}</div>
        </div>

        <div class="stat-block">
          <div class="stat-label">CODING TIME</div>
          <div class="stat-value neutral">{fmtDuration(data.total_duration_s)}</div>
        </div>

        <div class="stat-block">
          <div class="stat-label">FILES WRITTEN</div>
          <div class="stat-value neutral">{data.total_files_written}</div>
        </div>

        <div class="stat-block">
          <div class="stat-label">TOOL CALLS</div>
          <div class="stat-value neutral">{data.total_tool_calls.toLocaleString()}</div>
        </div>

      </div>
    </div>

    <!-- ── Pricing Assumptions (collapsible) ─────────────────────────────── -->
    <div class="pricing-section">
      <button
        class="pricing-toggle"
        on:click={() => (pricingOpen = !pricingOpen)}
        aria-expanded={pricingOpen}
      >
        <span class="toggle-label">PRICING ASSUMPTIONS</span>
        <span class="toggle-arrow" class:open={pricingOpen}>▾</span>
      </button>

      {#if pricingOpen}
        <div class="pricing-body">
          <div class="pricing-sub">Token estimation</div>
          <div class="pricing-row">
            <span>Input tokens / tool call</span>
            <span class="pricing-val">{INPUT_TOKENS_PER_CALL.toLocaleString()}</span>
          </div>
          <div class="pricing-row">
            <span>Output tokens / tool call</span>
            <span class="pricing-val">{OUTPUT_TOKENS_PER_CALL.toLocaleString()}</span>
          </div>
          <div class="pricing-note">
            Conservative estimates based on real Forge dispatch data. Actual usage may vary
            depending on context window size and prompt complexity.
          </div>

          <div class="pricing-sub" style="margin-top:10px;">Cloud rates (per M tokens, 2026)</div>
          <div class="pricing-row">
            <span>Claude Opus 4 input</span>
            <span class="pricing-val">${CLAUDE_OPUS_INPUT_PER_M.toFixed(2)}</span>
          </div>
          <div class="pricing-row">
            <span>Claude Opus 4 output</span>
            <span class="pricing-val">${CLAUDE_OPUS_OUTPUT_PER_M.toFixed(2)}</span>
          </div>
          <div class="pricing-row">
            <span>GPT-4o input</span>
            <span class="pricing-val">${GPT4O_INPUT_PER_M.toFixed(2)}</span>
          </div>
          <div class="pricing-row">
            <span>GPT-4o output</span>
            <span class="pricing-val">${GPT4O_OUTPUT_PER_M.toFixed(2)}</span>
          </div>

          <div class="pricing-sub" style="margin-top:10px;">Local cost</div>
          <div class="pricing-row">
            <span>Lemonade (self-hosted)</span>
            <span class="pricing-val free">$0.00</span>
          </div>
          <div class="pricing-note">
            Hardware and electricity not included. Assumes existing hardware investment.
          </div>
        </div>
      {/if}
    </div>

  {:else}
    <div class="state-msg">No data available. Pass a project <code>slug</code> prop.</div>
  {/if}

</div>

<!-- ═══════════════════════════════════════════════════════════════════════════
     STYLES
════════════════════════════════════════════════════════════════════════════ -->
<style>
  /* ── Panel shell ── */
  .cost-panel {
    height: 100%;
    display: flex;
    flex-direction: column;
    gap: 14px;
    font-family: var(--font-ui, sans-serif);
  }

  /* ── Header ── */
  .panel-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 8px;
    flex-wrap: wrap;
  }

  .header-left {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .panel-title {
    font-size: var(--text-section, 11px);
    font-weight: 600;
    color: var(--color-text-secondary, rgba(255,255,255,0.65));
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }

  .panel-subtitle {
    font-size: 11px;
    color: var(--color-text-muted, rgba(255,255,255,0.35));
    letter-spacing: 0.03em;
  }

  .project-badge {
    font-size: 11px;
    color: var(--color-text-muted, rgba(255,255,255,0.35));
    background: rgba(255,255,255,0.05);
    padding: 2px 8px;
    border-radius: var(--radius-badge, 10px);
    white-space: nowrap;
    align-self: flex-start;
  }

  /* ── Cards row ── */
  .cards-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
  }

  .cost-card {
    background: var(--color-bg-card, rgba(255,255,255,0.04));
    border-radius: 10px;
    padding: 12px 14px;
    display: flex;
    flex-direction: column;
    gap: 4px;
    border: 1px solid transparent;
    transition: box-shadow 0.2s ease, border-color 0.2s ease;
  }

  .cost-card:hover {
    box-shadow: 0 0 14px rgba(255,255,255,0.06);
    border-color: rgba(255,255,255,0.08);
  }

  .cloud-card {
    border-color: rgba(255, 100, 80, 0.12);
  }

  .cloud-card:hover {
    box-shadow: 0 0 16px rgba(255, 100, 80, 0.12);
    border-color: rgba(255, 100, 80, 0.25);
  }

  .local-card {
    border-color: rgba(80, 220, 140, 0.12);
  }

  .local-card:hover {
    box-shadow: 0 0 16px rgba(80, 220, 140, 0.15);
    border-color: rgba(80, 220, 140, 0.3);
  }

  .card-provider {
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--color-text-muted, rgba(255,255,255,0.38));
  }

  .card-model {
    font-size: 13px;
    font-weight: 600;
    color: var(--color-text-primary, #fff);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .card-cost {
    font-size: 20px;
    font-weight: 700;
    font-family: var(--font-mono, monospace);
    font-variant-numeric: tabular-nums;
    margin-top: 4px;
    line-height: 1;
  }

  .cloud-cost {
    color: #ff7c6a;
  }

  .local-cost {
    color: #50dc8c;
  }

  .card-tokens {
    display: flex;
    flex-direction: column;
    gap: 1px;
    margin-top: 4px;
  }

  .token-line {
    font-size: 10px;
    color: var(--color-text-muted, rgba(255,255,255,0.35));
    font-family: var(--font-mono, monospace);
  }

  .free-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    margin-top: 6px;
    padding: 3px 10px;
    background: rgba(80, 220, 140, 0.15);
    color: #50dc8c;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.1em;
    border-radius: var(--radius-badge, 10px);
    border: 1px solid rgba(80, 220, 140, 0.3);
    align-self: flex-start;
  }

  /* ── Savings bar ── */
  .savings-bar {
    display: flex;
    align-items: center;
    gap: 6px;
    background: rgba(80, 220, 140, 0.08);
    border: 1px solid rgba(80, 220, 140, 0.2);
    border-radius: 8px;
    padding: 10px 14px;
    flex-wrap: wrap;
  }

  .savings-label {
    font-size: 12px;
    color: var(--color-text-muted, rgba(255,255,255,0.45));
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .savings-amount {
    font-size: 20px;
    font-weight: 700;
    font-family: var(--font-mono, monospace);
    font-variant-numeric: tabular-nums;
    color: #50dc8c;
  }

  .savings-pct {
    font-size: 16px;
    font-weight: 600;
    color: #50dc8c;
    opacity: 0.8;
  }

  .savings-vs {
    font-size: 11px;
    color: var(--color-text-muted, rgba(255,255,255,0.35));
    margin-left: auto;
    white-space: nowrap;
  }

  /* ── Project stats ── */
  .stats-section {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .stats-title {
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--color-text-muted, rgba(255,255,255,0.38));
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
  }

  .stat-block {
    background: rgba(255,255,255,0.04);
    border-radius: 8px;
    padding: 9px 11px;
    display: flex;
    flex-direction: column;
    gap: 3px;
  }

  .stat-label {
    font-size: 9px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--color-text-muted, rgba(255,255,255,0.38));
  }

  .stat-value {
    font-size: 18px;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
    line-height: 1.1;
  }

  .stat-value.neutral {
    color: var(--color-text-primary, #fff);
  }

  /* ── Pricing assumptions (collapsible) ── */
  .pricing-section {
    margin-top: auto;
  }

  .pricing-toggle {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    background: none;
    border: none;
    border-top: 1px solid rgba(255,255,255,0.07);
    padding: 8px 0 4px;
    cursor: pointer;
    color: inherit;
  }

  .toggle-label {
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--color-text-muted, rgba(255,255,255,0.38));
  }

  .toggle-arrow {
    font-size: 12px;
    color: var(--color-text-muted, rgba(255,255,255,0.38));
    transition: transform 0.2s ease;
    display: inline-block;
  }

  .toggle-arrow.open {
    transform: rotate(180deg);
  }

  .pricing-body {
    display: flex;
    flex-direction: column;
    gap: 3px;
    padding: 8px 0 4px;
  }

  .pricing-sub {
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: var(--color-text-muted, rgba(255,255,255,0.38));
    margin-bottom: 2px;
  }

  .pricing-row {
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    color: var(--color-text-secondary, rgba(255,255,255,0.6));
    padding: 2px 0;
  }

  .pricing-val {
    font-family: var(--font-mono, monospace);
    color: var(--color-text-primary, #fff);
  }

  .pricing-val.free {
    color: #50dc8c;
  }

  .pricing-note {
    font-size: 10px;
    color: var(--color-text-muted, rgba(255,255,255,0.3));
    line-height: 1.5;
    margin-top: 3px;
    font-style: italic;
  }

  /* ── State messages ── */
  .state-msg {
    font-size: 13px;
    color: var(--color-text-muted, rgba(255,255,255,0.4));
    padding: 24px 0;
    text-align: center;
  }

  .state-msg.error {
    color: #ff7c6a;
  }

  .state-msg code {
    font-family: var(--font-mono, monospace);
    background: rgba(255,255,255,0.07);
    padding: 1px 5px;
    border-radius: 4px;
  }
</style>
