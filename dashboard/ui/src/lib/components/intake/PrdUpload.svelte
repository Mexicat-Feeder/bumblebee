<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  
  export let disabled: boolean = false;
  export let uploadedFilename: string | null = null;
  export let pastedText: string = '';
  
  const dispatch = createEventDispatcher<{
    file: { file: File };
    paste: { text: string };
    clear: void;
  }>();
  
  let mode: 'upload' | 'paste' = 'upload';
  let dragging = false;
  let fileInput: HTMLInputElement;
  
  function handleDrop(e: DragEvent) {
    e.preventDefault();
    dragging = false;
    const file = e.dataTransfer?.files[0];
    if (file) validateAndEmit(file);
  }
  
  function handleFileInput(e: Event) {
    const input = e.target as HTMLInputElement;
    const file = input.files?.[0];
    if (file) validateAndEmit(file);
  }
  
  function validateAndEmit(file: File) {
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!['md', 'txt', 'pdf'].includes(ext || '')) {
      alert('Please upload a .md, .txt, or .pdf file');
      return;
    }
    dispatch('file', { file });
  }
  
  function onPasteInput(e: Event) {
    const val = (e.target as HTMLTextAreaElement).value;
    dispatch('paste', { text: val });
  }
  
  function clearFile() {
    dispatch('clear');
  }
</script>

<div class="panel">
  <div class="panel-header">
    <h2 class="panel-title">PRODUCT REQUIREMENTS</h2>
  </div>

  <div class="input-area">
    <div class="tab-row">
      <button
        class="tab {mode === 'upload' ? 'tab-active' : 'tab-inactive'}"
        on:click={() => mode = 'upload'}
        disabled={disabled}
      >
        Upload file
      </button>
      <button
        class="tab {mode === 'paste' ? 'tab-active' : 'tab-inactive'}"
        on:click={() => mode = 'paste'}
        disabled={disabled}
      >
        Paste text
      </button>
    </div>

    {#if mode === 'upload'}
      {#if uploadedFilename}
        <div class="file-chip">
          <span class="file-chip-name">{uploadedFilename}</span>
          <button class="file-chip-remove" on:click={clearFile} disabled={disabled}>×</button>
        </div>
      {:else}
        <div
          class="upload-zone {dragging ? 'dragging' : ''}"
          on:dragover|preventDefault
          on:dragleave={() => dragging = false}
          on:drop={handleDrop}
          on:click={() => fileInput.click()}
        >
          <input
            type="file"
            accept=".md,.txt,.pdf"
            class="hidden-file-input"
            bind:this={fileInput}
            on:change={handleFileInput}
            disabled={disabled}
          />
          <div class="upload-icon">📄</div>
          <p class="upload-text">
            Drop your PRD here <span class="upload-browse">or browse</span>
          </p>
        </div>
      {/if}
    {:else}
      <textarea
        class="prd-textarea"
        placeholder="Paste your PRD content here..."
        bind:value={pastedText}
        on:input={onPasteInput}
        disabled={disabled}
      ></textarea>
    {/if}
  </div>
</div>

<style>
  .panel {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-panel);
    overflow: hidden;
  }

  .panel-header {
    padding: 16px 20px;
    border-bottom: 1px solid var(--border-subtle);
  }

  .panel-title {
    margin: 0;
    font-size: var(--text-sm);
    font-weight: 600;
    color: var(--color-text-primary);
    letter-spacing: 0.05em;
    text-transform: uppercase;
  }

  .input-area {
    padding: 16px 20px 20px;
  }

  .tab-row {
    display: flex;
    gap: 0;
    margin-bottom: 16px;
  }

  .tab {
    padding: 8px 16px;
    font-size: var(--text-sm);
    font-family: var(--font-sans);
    border: none;
    border-radius: var(--radius-badge);
    cursor: pointer;
    transition: border-color 200ms, color 200ms, background 200ms;
    border-bottom: 2px solid transparent;
    background: transparent;
    color: var(--color-text-secondary);
  }

  .tab:hover {
    background: rgba(58, 190, 255, 0.05);
  }

  .tab-active {
    border-bottom-color: var(--color-accent-primary);
    color: var(--color-text-primary);
    font-weight: 500;
  }

  .tab-inactive {
    border-bottom-color: transparent;
    color: var(--color-text-secondary);
  }

  .tab:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .upload-zone {
    border: 1.5px dashed rgba(58, 190, 255, 0.30);
    border-radius: var(--radius-panel);
    background: rgba(58, 190, 255, 0.03);
    padding: 40px 24px;
    text-align: center;
    cursor: pointer;
    transition: border-color 200ms, background 200ms;
  }

  .upload-zone.dragging {
    border-color: rgba(58, 190, 255, 0.70);
    background: rgba(58, 190, 255, 0.07);
  }

  .upload-icon {
    font-size: 32px;
    margin-bottom: 12px;
  }

  .upload-text {
    margin: 0;
    font-size: var(--text-sm);
    color: var(--color-text-secondary);
  }

  .upload-browse {
    color: var(--color-accent-primary);
    text-decoration: underline;
    cursor: pointer;
  }

  .hidden-file-input {
    position: absolute;
    width: 0;
    height: 0;
    opacity: 0;
    overflow: hidden;
  }

  .file-chip {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    background: var(--bg-card);
    border: 1.5px solid rgba(58, 190, 255, 0.50);
    border-radius: var(--radius-badge);
  }

  .file-chip-name {
    font-size: var(--text-sm);
    color: var(--color-text-primary);
    font-family: var(--font-mono);
    max-width: 300px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .file-chip-remove {
    background: none;
    border: none;
    color: var(--color-text-secondary);
    font-size: 18px;
    cursor: pointer;
    padding: 0 4px;
    line-height: 1;
    transition: color 200ms;
  }

  .file-chip-remove:hover {
    color: var(--color-danger);
  }

  .prd-textarea {
    width: 100%;
    min-height: 200px;
    resize: vertical;
    font-family: var(--font-mono);
    font-size: var(--text-mono);
    line-height: 1.7;
    padding: 12px 16px;
    background: var(--bg-input);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-input);
    color: var(--color-text-primary);
    outline: none;
    transition: border-color 200ms, box-shadow 200ms;
    box-sizing: border-box;
  }

  .prd-textarea:focus {
    border-color: var(--color-accent-primary);
    box-shadow: 0 0 0 2px rgba(58, 190, 255, 0.15);
  }

  .prd-textarea::placeholder {
    color: var(--color-text-secondary);
  }

  .prd-textarea:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style>
