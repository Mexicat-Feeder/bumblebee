<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  
  export let targetSystem: string = 'local';
  export let disabled: boolean = false;
  
  const dispatch = createEventDispatcher<{
    change: { field: string; value: string };
  }>();
  
  function onSelect(e: Event) {
    dispatch('change', { field: 'targetSystem', value: (e.target as HTMLSelectElement).value });
  }
</script>

<section class="settings-section">
  <h2 class="section-header">SETTINGS</h2>

  <div class="form-field">
    <label class="form-label">TARGET SYSTEM</label>
    <select
      class="form-select"
      bind:value={targetSystem}
      disabled={disabled}
      on:change={onSelect}
    >
      <option value="local">This machine</option>
    </select>
    <p class="settings-note">Additional targets will be available when network nodes are configured.</p>
  </div>
</section>

<style>
  .settings-section {
    background: var(--bg-card, #16202E);
    border: 1px solid rgba(58, 190, 255, 0.12);
    border-radius: 12px;
    padding: 20px;
  }

  .section-header {
    font-family: var(--font-ui);
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--color-text-primary, #E6EDF3);
    margin: 0 0 16px 0;
  }

  .form-field {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .form-label {
    font-family: var(--font-ui);
    font-size: 0.75rem;
    font-weight: 500;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--color-text-secondary, #8B9DC3);
  }

  .form-select {
    background: #1E2D42;
    border: 1px solid rgba(58, 190, 255, 0.20);
    border-radius: 8px;
    padding: 12px 40px 12px 16px;
    height: 44px;
    color: var(--color-text-primary, #E6EDF3);
    font-family: var(--font-ui);
    font-size: 0.9rem;
    width: 100%;
    box-sizing: border-box;
    appearance: none;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%236B7A8D' fill='none' stroke-width='1.5'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 16px center;
    cursor: pointer;
    transition: border-color 200ms ease, box-shadow 200ms ease;
  }

  .form-select:focus {
    border-color: rgba(58, 190, 255, 0.65);
    box-shadow: 0 0 0 3px rgba(58, 190, 255, 0.10);
    outline: none;
  }

  .form-select:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .settings-note {
    font-size: 0.75rem;
    color: var(--color-text-muted, #6B7A8D);
    margin-top: 8px;
  }
</style>
