<script lang="ts">
  import { researchStore, selectedResearchId, researchView } from '$lib/stores/research';

  let question = '';
  let context = '';
  let priority = 5;
  let loading = false;
  let error = '';
  let submitted = false;
  let submittedId = '';

  async function submit() {
    if (!question.trim()) { error = 'Please enter a research question.'; return; }
    loading = true; error = '';
    try {
      const res = await fetch('/api/research/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: question.trim(), context: context.trim(), priority }),
      });
      if (!res.ok) {
        let msg = res.statusText;
        try { const d = await res.json(); msg = d.detail || msg; } catch { /* plain-text error */ }
        throw new Error(msg);
      }
      const data = await res.json();
      submitted = true;
      submittedId = data.ticket_id;
      await researchStore.fetchTickets();
    } catch (e: any) {
      error = e.message ?? 'Submit failed';
    }
    loading = false;
  }
</script>

<div class="research-intake">
  <div class="intake-header">
    <h1 class="intake-title">New Research Request</h1>
    <p class="intake-sub">Submit a question to the Sift research queue. Pixel will investigate and write a report.</p>
  </div>

  {#if error}
    <div class="error-banner">{error}</div>
  {/if}

  {#if submitted}
  <div class="success-card">
    <div class="success-icon">&#x2705;</div>
    <h2 class="success-title">Research Queued</h2>
    <p class="success-sub"><strong>{submittedId}</strong> has been added to the Sift queue. It will be picked up automatically.</p>
    <button class="another-btn" on:click={() => { submitted = false; question = ''; context = ''; submittedId = ''; }}>
      Submit Another
    </button>
  </div>
  {:else}
  <div class="form-card">
    <label class="field-label" for="question">Research Question <span class="required">*</span></label>
    <textarea
      id="question"
      class="field-textarea"
      rows={4}
      placeholder="What do you want Pixel to research?"
      bind:value={question}
      disabled={loading}
    ></textarea>

    <label class="field-label" for="context">Context / Background <span class="optional">(optional)</span></label>
    <textarea
      id="context"
      class="field-textarea field-textarea--sm"
      rows={3}
      placeholder="Any relevant background, constraints, or prior decisions…"
      bind:value={context}
      disabled={loading}
    ></textarea>

    <label class="field-label" for="priority">Priority</label>
    <select id="priority" class="field-select" bind:value={priority} disabled={loading}>
      <option value={1}>High (1)</option>
      <option value={5}>Medium (5)</option>
      <option value={10}>Low (10)</option>
    </select>

    <button class="submit-btn" on:click={submit} disabled={loading || !question.trim()}>
      {loading ? 'Submitting…' : 'Submit to Queue'}
    </button>
  </div>
  {/if}
</div>

<style>
  .research-intake {
    max-width: 640px;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    gap: 20px;
    padding-bottom: 40px;
  }

  .intake-header { margin-bottom: 4px; }

  .intake-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--color-text-primary);
    margin: 0 0 6px;
  }

  .intake-sub {
    font-size: 13px;
    color: var(--color-text-muted);
    margin: 0;
  }

  .error-banner {
    background: rgba(255, 107, 107, 0.1);
    border: 1px solid rgba(255, 107, 107, 0.3);
    border-radius: 8px;
    padding: 10px 14px;
    color: #ff6b6b;
    font-size: 13px;
  }

  .form-card {
    background: var(--color-bg-panel);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: var(--radius-panel);
    padding: 20px 24px;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .field-label {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: var(--color-text-muted);
  }

  .required { color: #ff6b6b; margin-left: 2px; }
  .optional { color: var(--color-text-muted); font-weight: 400; text-transform: none; letter-spacing: 0; }

  .field-textarea, .field-select {
    width: 100%;
    box-sizing: border-box;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 6px;
    color: var(--color-text-primary);
    font-family: var(--font-ui);
    font-size: 13px;
    padding: 10px 12px;
    resize: vertical;
    transition: border-color 0.15s;
  }

  .field-textarea--sm { resize: vertical; }

  .field-textarea:focus, .field-select:focus {
    outline: none;
    border-color: var(--color-accent-primary);
  }

  .field-select { resize: none; cursor: pointer; }

  .submit-btn {
    align-self: flex-start;
    padding: 10px 24px;
    background: var(--color-accent-primary);
    border: none;
    border-radius: var(--radius-badge);
    color: #000;
    font-family: var(--font-ui);
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.15s;
  }

  .submit-btn:disabled { opacity: 0.45; cursor: not-allowed; }
  .submit-btn:hover:not(:disabled) { opacity: 0.85; }

  .success-card {
    background: var(--color-bg-panel);
    border: 1px solid rgba(89, 227, 138, 0.2);
    border-radius: var(--radius-panel);
    padding: 32px 24px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
    text-align: center;
  }

  .success-icon { font-size: 36px; }

  .success-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--color-text-primary);
    margin: 0;
  }

  .success-sub {
    font-size: 13px;
    color: var(--color-text-muted);
    margin: 0;
    line-height: 1.5;
  }

  .another-btn {
    margin-top: 8px;
    padding: 8px 20px;
    background: transparent;
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: var(--radius-badge);
    color: var(--color-text-secondary);
    font-family: var(--font-ui);
    font-size: 13px;
    cursor: pointer;
    transition: border-color 0.15s, color 0.15s;
  }

  .another-btn:hover {
    border-color: rgba(255, 255, 255, 0.3);
    color: var(--color-text-primary);
  }
</style>
