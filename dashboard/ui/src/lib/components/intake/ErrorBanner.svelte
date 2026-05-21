<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  
  export let message: string = '';
  export let type: 'error' | 'warning' | 'info' = 'error';
  export let dismissible: boolean = true;
  export let retryable: boolean = false;
  
  const dispatch = createEventDispatcher<{
    dismiss: void;
    retry: void;
  }>();
  
  let visible = true;
  
  function dismiss() {
    visible = false;
    dispatch('dismiss');
  }
  
  function retry() {
    dispatch('retry');
  }
  
  // Reset visibility when message changes
  $: if (message) visible = true;
</script>

{#if visible && message}
  <div class="banner banner--{type}" role="alert">
    <span class="banner-icon">
      {#if type === 'error'}⚠{:else if type === 'warning'}⚡{:else}ℹ{/if}
    </span>
    <span class="banner-message">{message}</span>
    <div class="banner-actions">
      {#if retryable}
        <button class="banner-btn" on:click={retry}>Retry</button>
      {/if}
      {#if dismissible}
        <button class="banner-dismiss" on:click={dismiss}>×</button>
      {/if}
    </div>
  </div>
{/if}

<style>
  .banner {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    border-radius: var(--radius-badge);
    margin-bottom: 16px;
    font-size: var(--text-body);
  }

  .banner--error {
    background: rgba(255, 107, 107, 0.10);
    border: 1px solid rgba(255, 107, 107, 0.30);
    color: var(--color-alert-blocked);
  }

  .banner--warning {
    background: rgba(255, 170, 74, 0.10);
    border: 1px solid rgba(255, 170, 74, 0.30);
    color: var(--color-alert-warning);
  }

  .banner--info {
    background: rgba(58, 190, 255, 0.10);
    border: 1px solid rgba(58, 190, 255, 0.30);
    color: var(--color-accent-primary);
  }

  .banner-icon {
    font-size: 1rem;
    flex-shrink: 0;
  }

  .banner-message {
    flex: 1;
  }

  .banner-actions {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
  }

  .banner-btn {
    background: transparent;
    border: 1px solid currentColor;
    border-radius: var(--radius-badge);
    padding: 4px 12px;
    color: inherit;
    font-size: 0.75rem;
    cursor: pointer;
    font-family: var(--font-ui);
  }

  .banner-btn:hover {
    background: rgba(255, 255, 255, 0.05);
  }

  .banner-dismiss {
    background: transparent;
    border: none;
    color: inherit;
    font-size: 1.1rem;
    cursor: pointer;
    padding: 0 4px;
    opacity: 0.6;
  }

  .banner-dismiss:hover {
    opacity: 1;
  }
</style>
