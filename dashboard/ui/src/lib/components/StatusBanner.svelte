<script lang="ts">
  import { connection } from '$lib/stores/connection';

  $: downServices = $connection.services.filter(s => !s.ok);
  $: showBanner = !$connection.reachable || !$connection.healthy;
</script>

{#if showBanner}
<div class="status-banner" class:banner-unreachable={!$connection.reachable} class:banner-degraded={$connection.reachable && !$connection.healthy}>
  <span class="status-icon">⚠</span>
  {#if !$connection.reachable}
    <span>Backend unreachable — dashboard data may be stale</span>
  {:else}
    <span>Services offline: {downServices.map(s => s.name).join(', ')}</span>
  {/if}
</div>
{/if}

<style>
  .status-banner {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 20px;
    border-radius: var(--radius-badge);
    font-size: var(--text-body);
    color: var(--color-text-primary);
  }

  .banner-unreachable {
    background: color-mix(in srgb, var(--color-alert-blocked) 15%, transparent);
    border-left: 3px solid var(--color-alert-blocked);
  }

  .banner-degraded {
    background: color-mix(in srgb, var(--color-alert-warning) 15%, transparent);
    border-left: 3px solid var(--color-alert-warning);
  }

  .status-icon {
    font-size: 1.1rem;
    flex-shrink: 0;
  }
</style>
