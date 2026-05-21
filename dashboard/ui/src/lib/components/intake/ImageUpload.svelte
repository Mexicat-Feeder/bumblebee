<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  export let images: Array<{ url: string; name: string }> = [];
  export let disabled: boolean = false;
  export let maxImages: number = 5;

  let fileInput: HTMLInputElement;

  const dispatch = createEventDispatcher<{
    add: { files: FileList };
    remove: { index: number };
  }>();

  function handleFileInput(e: Event) {
    const input = e.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      dispatch('add', { files: input.files });
      input.value = '';
    }
  }

  function removeImage(index: number) {
    dispatch('remove', { index });
  }
</script>

<div class="section-panel">
  <div class="section-header">
    <h3 class="section-title">VISUAL REFERENCES</h3>
    <span class="section-subtitle">(optional)</span>
  </div>

  <div class="image-grid">
    {#each images as image, index}
      <div class="image-slot">
        <img src={image.url} alt={image.name} />
        <button class="remove-btn" on:click={() => removeImage(index)}>×</button>
      </div>
    {/each}

    {#if images.length < maxImages}
      <div
        class="image-slot image-slot--empty"
        class:disabled
        on:click={() => !disabled && fileInput?.click()}
      >
        <span class="plus-icon">+</span>
      </div>
    {/if}
  </div>

  <input
    type="file"
    accept=".png,.jpg,.jpeg,.webp"
    multiple
    on:change={handleFileInput}
    class="file-input-hidden"
    bind:this={fileInput}
  />
</div>

<style>
  .section-panel {
    background: var(--bg-card);
    border-radius: var(--radius-panel);
    padding: 16px;
  }

  .section-header {
    display: flex;
    align-items: baseline;
    gap: 8px;
    margin-bottom: 16px;
  }

  .section-title {
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--color-text-primary);
    margin: 0;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .section-subtitle {
    font-size: 0.75rem;
    color: var(--color-text-muted);
  }

  .image-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 12px;
  }

  .image-slot {
    aspect-ratio: 1;
    border-radius: var(--radius-panel);
    overflow: hidden;
    position: relative;
  }

  .image-slot--empty {
    border: 1.5px dashed rgba(58, 190, 255, 0.20);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: border-color 200ms;
  }

  .image-slot--empty:hover {
    border-color: rgba(58, 190, 255, 0.50);
  }

  .image-slot--empty.disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .image-slot--empty.disabled:hover {
    border-color: rgba(58, 190, 255, 0.20);
  }

  .image-slot img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .remove-btn {
    position: absolute;
    top: 4px;
    right: 4px;
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background: var(--color-alert-blocked);
    color: white;
    border: none;
    font-size: 0.75rem;
    cursor: pointer;
    display: none;
    align-items: center;
    justify-content: center;
  }

  .image-slot:hover .remove-btn {
    display: flex;
  }

  .plus-icon {
    font-size: 1.5rem;
    color: var(--color-text-muted);
  }

  .file-input-hidden {
    position: absolute;
    width: 0;
    height: 0;
    opacity: 0;
    overflow: hidden;
  }

  @media (max-width: 600px) {
    .image-grid {
      grid-template-columns: repeat(3, 1fr);
    }
  }
</style>
