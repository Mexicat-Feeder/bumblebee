<script lang="ts">
  export let status: string = 'intake';
  export let techStack: string | null = null;
  export let visualSpec: string | null = null;
  export let architectureSummary: string | null = null;
  export let lastPolled: Date | null = null;
  
  $: showPlaceholder = status === 'qa_pending' && !techStack && !visualSpec && !architectureSummary;
  $: showOutputs = techStack || visualSpec || architectureSummary;
  $: techPills = techStack ? techStack.split(/[+·,]/).map(s => s.trim()).filter(Boolean) : [];
  
  function formatTime(d: Date | null): string {
    if (!d) return 'never';
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
</script>

{#if showPlaceholder}
  <div class="output-placeholder">
    <div class="placeholder-icon">🔄</div>
    <div class="placeholder-title">Pixel is working on it</div>
    <p class="placeholder-text">
      The Q&A is in progress in Telegram. When Pixel finishes, the outputs will appear here automatically.
    </p>
    <div class="placeholder-footer">
      <span class="placeholder-check">last checked: {formatTime(lastPolled)}</span>
    </div>
  </div>
{/if}

{#if showOutputs}
  <div class="output-panels">
    {#if techStack}
      <div class="output-panel fade-in">
        <div class="output-label">TECH STACK</div>
        <div class="tech-pills">
          {#each techPills as pill}
            <span class="tech-pill">{pill}</span>
          {/each}
        </div>
      </div>
    {/if}

    {#if visualSpec}
      <div class="output-panel fade-in">
        <div class="output-label">DESIGN INTENT</div>
        <div class="output-content">{visualSpec}</div>
      </div>
    {/if}

    {#if architectureSummary}
      <div class="output-panel fade-in">
        <div class="output-label">ARCHITECTURE SUMMARY</div>
        <div class="output-content">{architectureSummary}</div>
      </div>
    {/if}
  </div>
{/if}

<style>
  .output-panels {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .fade-in {
    animation: fade-in 400ms ease forwards;
  }

  @keyframes fade-in {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }

  .output-panel {
    background: var(--color-bg-panel);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: var(--radius-panel);
    box-shadow: 0 4px 32px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.04);
    padding: var(--spacing-panel-pad);
    border-left: 4px solid var(--color-accent-complete);
    padding-left: 20px;
  }

  .output-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--color-accent-complete);
    margin-bottom: 10px;
  }

  .output-content {
    color: var(--color-text-primary);
    font-family: var(--font-ui);
    font-size: var(--text-body);
    line-height: 1.6;
    white-space: pre-wrap;
    max-height: 320px;
    overflow-y: auto;
  }

  .tech-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .tech-pill {
    background: rgba(58, 190, 255, 0.12);
    border: 1px solid rgba(58, 190, 255, 0.25);
    border-radius: var(--radius-pill);
    padding: 3px 10px;
    font-size: 0.75rem;
    color: var(--color-accent-primary);
  }

  .output-placeholder {
    background: var(--color-bg-panel);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: var(--radius-panel);
    box-shadow: 0 4px 32px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.04);
    padding: 40px var(--spacing-panel-pad);
    border-left: 4px solid var(--color-accent-complete);
    text-align: center;
    animation: border-pulse 2s ease-in-out infinite;
  }

  @keyframes border-pulse {
    0%, 100% { border-left-color: rgba(45, 230, 230, 0.4); }
    50% { border-left-color: rgba(45, 230, 230, 1); }
  }

  .placeholder-icon {
    font-size: 1.5rem;
    margin-bottom: 12px;
  }

  .placeholder-title {
    font-size: 1rem;
    font-weight: 600;
    color: var(--color-text-primary);
    margin-bottom: 8px;
  }

  .placeholder-text {
    color: var(--color-text-secondary);
    font-size: var(--text-body);
    max-width: 480px;
    margin: 0 auto 16px;
  }

  .placeholder-footer {
    display: flex;
    justify-content: center;
  }

  .placeholder-check {
    font-size: 0.75rem;
    color: var(--color-text-muted);
  }
</style>
