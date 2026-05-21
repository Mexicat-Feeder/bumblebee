<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  
  export let name: string = '';
  export let slug: string = '';
  export let description: string = '';
  export let codeFolder: string = '';
  export let disabled: boolean = false;
  
  const dispatch = createEventDispatcher<{
    change: { field: string; value: string };
  }>();
  
  function autoSlug(name: string): string {
    return name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  }
  
  let slugEdited = false;
  
  function onNameChange(e: Event) {
    const val = (e.target as HTMLInputElement).value;
    dispatch('change', { field: 'name', value: val });
    if (!slugEdited) {
      const s = autoSlug(val);
      dispatch('change', { field: 'slug', value: s });
      dispatch('change', { field: 'codeFolder', value: `./output/${s}` });
    }
  }
  
  function onSlugChange(e: Event) {
    slugEdited = true;
    dispatch('change', { field: 'slug', value: (e.target as HTMLInputElement).value });
  }
  
  function onDescChange(e: Event) {
    dispatch('change', { field: 'description', value: (e.target as HTMLInputElement).value });
  }
  
  function onFolderChange(e: Event) {
    dispatch('change', { field: 'codeFolder', value: (e.target as HTMLInputElement).value });
  }
</script>

<div class="section-panel">
  <h3 class="section-header">PROJECT IDENTITY</h3>

  <div class="form-grid-2">
    <div>
      <label class="form-label">Project Name</label>
      <input
        type="text"
        class="form-input"
        bind:value={name}
        on:input={onNameChange}
        disabled={disabled}
        placeholder="Enter project name"
      />
    </div>
    <div>
      <label class="form-label">Project ID</label>
      <input
        type="text"
        class="form-input"
        bind:value={slug}
        on:input={onSlugChange}
        disabled={disabled}
        class:slug-auto={!slugEdited}
        placeholder="Auto-generated from name"
      />
    </div>
  </div>

  <div style="margin-top: 16px;">
    <label class="form-label">Description</label>
    <input
      type="text"
      class="form-input"
      bind:value={description}
      on:input={onDescChange}
      disabled={disabled}
      placeholder="One-line description of this project"
    />
  </div>

  <div style="margin-top: 16px;">
    <label class="form-label">Code Folder</label>
    <input
      type="text"
      class="form-input"
      bind:value={codeFolder}
      on:input={onFolderChange}
      disabled={disabled}
      placeholder="./output/{slug}"
    />
  </div>
</div>

<style>
  .section-panel {
    background: var(--color-bg-panel);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: var(--radius-panel);
    box-shadow: 0 4px 32px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.04);
    padding: var(--spacing-panel-pad);
  }

  .section-header {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--color-text-secondary);
    margin: 0 0 20px 0;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(255,255,255,0.06);
  }

  .form-input {
    background: #1E2D42;
    border: 1px solid rgba(58, 190, 255, 0.20);
    border-radius: 8px;
    padding: 12px 16px;
    height: 44px;
    color: var(--color-text-primary);
    font-family: var(--font-ui);
    font-size: 0.9rem;
    transition: border-color 200ms ease, box-shadow 200ms ease;
    width: 100%;
    box-sizing: border-box;
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

  .slug-auto {
    background: rgba(30, 45, 66, 0.6);
  }

  .form-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--color-text-secondary);
    margin-bottom: 6px;
    display: block;
  }

  .form-grid-2 {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }
</style>
