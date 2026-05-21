<script lang="ts">
  import { onMount, afterUpdate } from 'svelte';
  import { lemonadeLogStore } from '$lib/stores/lemonadeLogs';

  let terminalRef: HTMLDivElement;

  $: logLines = $lemonadeLogStore.lines || [];
  $: connected = $lemonadeLogStore.connected ?? false;

  onMount(() => {
    lemonadeLogStore.connect();
    if (terminalRef) terminalRef.scrollTop = terminalRef.scrollHeight;
  });

  afterUpdate(() => {
    if (terminalRef) terminalRef.scrollTop = terminalRef.scrollHeight;
  });
</script>

<div class="log-panel">
  <div class="log-header">
    <span class="log-title">LOCAL MODEL LOG</span>
    <span class="status-pill" class:status-live={connected} class:status-waiting={!connected}>
      <span class="status-dot"></span>
      {connected ? 'LIVE' : 'WAITING'}
    </span>
  </div>

  <div class="terminal" bind:this={terminalRef}>
    {#if logLines.length === 0}
      <span class="terminal-empty">[Waiting for inference activity...]</span>
    {:else}
      {#each logLines as line}
        <div class="log-line">{line}</div>
      {/each}
    {/if}
  </div>
</div>

<style>
  .log-panel {
    display: flex;
    flex-direction: column;
    gap: 12px;
    height: 100%;
  }

  .log-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .log-title {
    font-size: var(--text-section);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--color-text-secondary);
  }

  .status-pill {
    display: flex;
    align-items: center;
    gap: 5px;
    font-size: 0.6rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    padding: 2px 8px;
    border-radius: 10px;
  }

  .status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .status-live {
    color: var(--color-status-pass);
    background: rgba(89, 227, 138, 0.1);
  }

  .status-live .status-dot {
    background: var(--color-status-pass);
    box-shadow: 0 0 4px var(--color-status-pass);
  }

  .status-waiting {
    color: var(--color-text-muted);
    background: rgba(255, 255, 255, 0.05);
  }

  .status-waiting .status-dot {
    background: var(--color-text-muted);
  }

  .terminal {
    background: var(--color-bg-terminal);
    border-radius: var(--radius-badge);
    padding: 12px 16px;
    font-family: var(--font-mono);
    font-size: var(--text-mono);
    line-height: 1.6;
    color: var(--color-text-terminal);
    overflow-y: auto;
    /* ~25 lines: 25 × font-size(12px) × line-height(1.6) + padding */
    height: 420px;
  }

  .terminal-empty {
    color: var(--color-text-muted);
    font-style: italic;
  }

  .log-line {
    white-space: pre-wrap;
    word-break: break-word;
  }
</style>
