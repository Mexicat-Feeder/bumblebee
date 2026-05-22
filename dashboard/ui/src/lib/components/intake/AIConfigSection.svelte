<script lang="ts">
  import { createEventDispatcher, onMount } from 'svelte';

  export let disabled: boolean = false;

  // Per-phase model config
  export let qaModelSource: string = 'lemonade';
  export let qaModelId: string = '';
  export let decompModelSource: string = 'lemonade';
  export let decompModelId: string = '';
  export let forgeModelSource: string = 'custom';
  export let forgeModelId: string = '';
  export let visionModelSource: string = 'custom';
  export let visionModelId: string = '';

  // Custom API settings
  export let customApiBaseUrl: string = '';
  export let customApiKey: string = '';

  const dispatch = createEventDispatcher<{
    change: { field: string; value: string };
  }>();

  // Lemonade state
  let lemonadeConnected = false;
  let lemonadeModels: Array<{ id: string; name: string; loaded: boolean }> = [];
  let lemonadeChecking = true;

  onMount(() => {
    probeLemonade();
  });

  async function probeLemonade() {
    lemonadeChecking = true;
    try {
      const resp = await fetch('/api/ai/models');
      if (resp.ok) {
        const data = await resp.json();
        lemonadeConnected = data.lemonade?.connected ?? false;
        lemonadeModels = data.lemonade?.models ?? [];
        // Auto-select first loaded model if no model selected yet
        if (lemonadeConnected && lemonadeModels.length > 0) {
          const loaded = lemonadeModels.find(m => m.loaded);
          const best = loaded ?? lemonadeModels[0];
          if (!qaModelId) {
            qaModelId = best.id;
            dispatch('change', { field: 'qaModelId', value: best.id });
          }
          if (!decompModelId) {
            decompModelId = best.id;
            dispatch('change', { field: 'decompModelId', value: best.id });
          }
        }
      }
    } catch {
      lemonadeConnected = false;
    }
    lemonadeChecking = false;
  }

  function onSourceChange(phase: string, e: Event) {
    const value = (e.target as HTMLSelectElement).value;
    dispatch('change', { field: `${phase}ModelSource`, value });
  }

  function onModelChange(phase: string, e: Event) {
    const value = (e.target as HTMLSelectElement).value || (e.target as HTMLInputElement).value;
    dispatch('change', { field: `${phase}ModelId`, value });
  }

  function onCustomField(field: string, e: Event) {
    const value = (e.target as HTMLInputElement).value;
    dispatch('change', { field, value });
  }

  // Determine if custom API section should be visible
  $: needsCustomApi = forgeModelSource === 'custom' || visionModelSource === 'custom'
    || decompModelSource === 'custom' || qaModelSource === 'custom';

  interface PhaseConfig {
    key: string;
    label: string;
    description: string;
    source: string;
    modelId: string;
  }

  $: phases = [
    { key: 'qa', label: 'Q&A', description: 'PRD refinement chat', source: qaModelSource, modelId: qaModelId },
    { key: 'decomp', label: 'Decomposition', description: 'Ticket planning', source: decompModelSource, modelId: decompModelId },
    { key: 'forge', label: 'Coding', description: 'File generation', source: forgeModelSource, modelId: forgeModelId },
    { key: 'vision', label: 'Vision QA', description: 'Screenshot review', source: visionModelSource, modelId: visionModelId },
  ] as PhaseConfig[];
</script>

<section class="ai-config-section">
  <h2 class="section-header">AI CONFIGURATION</h2>

  <!-- Lemonade status -->
  <div class="lemonade-status" class:connected={lemonadeConnected} class:checking={lemonadeChecking}>
    <span class="status-dot"></span>
    {#if lemonadeChecking}
      <span class="status-text">Checking local AI...</span>
    {:else if lemonadeConnected}
      <span class="status-text">Local AI connected — {lemonadeModels.length} model{lemonadeModels.length !== 1 ? 's' : ''} available</span>
      <button class="refresh-btn" on:click={probeLemonade} title="Refresh models">↻</button>
    {:else}
      <span class="status-text">Local AI not detected</span>
      <button class="refresh-btn" on:click={probeLemonade} title="Retry connection">↻</button>
    {/if}
  </div>

  <!-- Per-phase model selectors -->
  <div class="phases-grid">
    {#each phases as phase}
      <div class="phase-row">
        <div class="phase-info">
          <span class="phase-label">{phase.label}</span>
          <span class="phase-desc">{phase.description}</span>
        </div>
        <div class="phase-controls">
          <select
            class="source-select"
            value={phase.source}
            on:change={(e) => onSourceChange(phase.key, e)}
            {disabled}
          >
            <option value="lemonade">Local AI</option>
            <option value="custom">Cloud / Custom API</option>
          </select>

          {#if phase.source === 'lemonade'}
            {#if lemonadeConnected && lemonadeModels.length > 0}
              <select
                class="model-select"
                value={phase.modelId}
                on:change={(e) => onModelChange(phase.key, e)}
                {disabled}
              >
                {#each lemonadeModels as model}
                  <option value={model.id}>
                    {model.name}{model.loaded ? ' ●' : ''}
                  </option>
                {/each}
              </select>
            {:else}
              <span class="no-models">No models available</span>
            {/if}
          {:else}
            <input
              type="text"
              class="model-input"
              value={phase.modelId}
              on:input={(e) => onModelChange(phase.key, e)}
              placeholder="e.g. gpt-4o"
              {disabled}
            />
          {/if}
        </div>
      </div>
    {/each}
  </div>

  <!-- Custom API settings (shown when any phase uses custom) -->
  {#if needsCustomApi}
    <div class="custom-api-section">
      <h3 class="subsection-header">CLOUD / CUSTOM API</h3>
      <div class="form-field">
        <label class="form-label">API Base URL</label>
        <input
          type="text"
          class="form-input"
          value={customApiBaseUrl}
          on:input={(e) => onCustomField('customApiBaseUrl', e)}
          placeholder="https://api.openai.com/v1"
          {disabled}
        />
      </div>
      <div class="form-field">
        <label class="form-label">API Key</label>
        <input
          type="password"
          class="form-input"
          value={customApiKey}
          on:input={(e) => onCustomField('customApiKey', e)}
          placeholder="sk-..."
          {disabled}
        />
      </div>
    </div>
  {/if}
</section>

<style>
  .ai-config-section {
    background: var(--bg-card, #16202E);
    border: 1px solid rgba(58, 190, 255, 0.12);
    border-radius: 12px;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .section-header {
    font-family: var(--font-ui);
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--color-text-primary, #E6EDF3);
    margin: 0;
  }

  /* Lemonade status indicator */
  .lemonade-status {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 14px;
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.06);
  }

  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #6B7A8D;
    flex-shrink: 0;
  }

  .lemonade-status.connected .status-dot {
    background: #3ABE55;
    box-shadow: 0 0 6px rgba(58, 190, 85, 0.4);
  }

  .lemonade-status.checking .status-dot {
    background: #F0B429;
    animation: pulse 1s ease-in-out infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 0.4; }
    50% { opacity: 1; }
  }

  .status-text {
    font-size: 0.8rem;
    color: var(--color-text-secondary, #8B9DC3);
    flex: 1;
  }

  .refresh-btn {
    background: none;
    border: 1px solid rgba(58, 190, 255, 0.2);
    border-radius: 4px;
    color: var(--color-text-secondary, #8B9DC3);
    cursor: pointer;
    padding: 2px 6px;
    font-size: 0.85rem;
    transition: border-color 150ms, color 150ms;
  }

  .refresh-btn:hover {
    border-color: rgba(58, 190, 255, 0.5);
    color: var(--color-text-primary, #E6EDF3);
  }

  /* Phase grid */
  .phases-grid {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .phase-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 14px;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 8px;
  }

  .phase-info {
    min-width: 120px;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .phase-label {
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--color-text-primary, #E6EDF3);
  }

  .phase-desc {
    font-size: 0.7rem;
    color: var(--color-text-muted, #6B7A8D);
  }

  .phase-controls {
    flex: 1;
    display: flex;
    gap: 8px;
    align-items: center;
  }

  .source-select,
  .model-select {
    background: #1E2D42;
    border: 1px solid rgba(58, 190, 255, 0.20);
    border-radius: 6px;
    padding: 8px 28px 8px 10px;
    color: var(--color-text-primary, #E6EDF3);
    font-family: var(--font-ui);
    font-size: 0.8rem;
    appearance: none;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6' viewBox='0 0 10 6'%3E%3Cpath d='M1 1l4 4 4-4' stroke='%236B7A8D' fill='none' stroke-width='1.5'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 10px center;
    cursor: pointer;
    transition: border-color 150ms;
  }

  .source-select { min-width: 140px; }
  .model-select { flex: 1; min-width: 0; }

  .source-select:focus,
  .model-select:focus {
    border-color: rgba(58, 190, 255, 0.65);
    outline: none;
  }

  .source-select:disabled,
  .model-select:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .model-input {
    flex: 1;
    min-width: 0;
    background: #1E2D42;
    border: 1px solid rgba(58, 190, 255, 0.20);
    border-radius: 6px;
    padding: 8px 10px;
    color: var(--color-text-primary, #E6EDF3);
    font-family: var(--font-ui);
    font-size: 0.8rem;
    transition: border-color 150ms;
  }

  .model-input:focus {
    border-color: rgba(58, 190, 255, 0.65);
    outline: none;
  }

  .model-input:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .no-models {
    font-size: 0.75rem;
    color: var(--color-text-muted, #6B7A8D);
    font-style: italic;
  }

  /* Custom API section */
  .custom-api-section {
    padding-top: 12px;
    border-top: 1px solid rgba(255, 255, 255, 0.06);
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .subsection-header {
    font-family: var(--font-ui);
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--color-text-secondary, #8B9DC3);
    margin: 0;
  }

  .form-field {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .form-label {
    font-family: var(--font-ui);
    font-size: 0.7rem;
    font-weight: 500;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--color-text-secondary, #8B9DC3);
  }

  .form-input {
    background: #1E2D42;
    border: 1px solid rgba(58, 190, 255, 0.20);
    border-radius: 8px;
    padding: 10px 14px;
    height: 40px;
    color: var(--color-text-primary, #E6EDF3);
    font-family: var(--font-ui);
    font-size: 0.85rem;
    width: 100%;
    box-sizing: border-box;
    transition: border-color 200ms ease, box-shadow 200ms ease;
  }

  .form-input:focus {
    border-color: rgba(58, 190, 255, 0.65);
    box-shadow: 0 0 0 3px rgba(58, 190, 255, 0.10);
    outline: none;
  }

  .form-input:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style>
