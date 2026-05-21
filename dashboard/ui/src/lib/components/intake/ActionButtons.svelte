<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  
  export let status: string = 'intake';
  export let checklist: {
    named: boolean;
    prd_uploaded: boolean;
    qa_complete: boolean;
    approved: boolean;
    scaffolded: boolean;
  } = { named: false, prd_uploaded: false, qa_complete: false, approved: false, scaffolded: false };
  export let loading: boolean = false;
  
  const dispatch = createEventDispatcher<{
    'begin-qa': void;
    'approve': void;
    'begin-build': void;
  }>();
  
  $: action = computeAction(status, checklist);
  
  function computeAction(st: string, cl: typeof checklist): { label: string; event: string; enabled: boolean } | null {
    if (st === 'intake') {
      return {
        label: 'Begin Q&A',
        event: 'begin-qa',
        enabled: cl.named && cl.prd_uploaded
      };
    }
    if (st === 'qa_pending') {
      return null;  // no action while Q&A is in progress
    }
    if (st === 'qa_complete') {
      return {
        label: 'Approve Plan',
        event: 'approve',
        enabled: cl.qa_complete
      };
    }
    if (st === 'approved') {
      return {
        label: 'Begin Build',
        event: 'begin-build',
        enabled: cl.approved
      };
    }
    // scaffolded or running — no more actions
    return null;
  }
  
  function onClick() {
    if (action && action.enabled && !loading) {
      dispatch(action.event as any);
    }
  }
</script>

{#if action}
  <div class="action-container">
    <button
      class="btn-primary"
      disabled={!action.enabled || loading}
      on:click={onClick}
    >
      {#if loading}
        <span class="btn-spinner"></span>
      {/if}
      {action.label}
    </button>
    {#if !action.enabled && status === 'intake'}
      <p class="action-hint">Fill in the project name and upload a PRD to continue.</p>
    {/if}
  </div>
{/if}

<style>
.action-container {
  margin-top: 20px;
}

.btn-primary {
  background: var(--color-accent-primary);
  color: #0B1220;
  border: none;
  border-radius: var(--radius-panel);
  height: 52px;
  font-size: 0.95rem;
  font-weight: 600;
  letter-spacing: 0.03em;
  width: 100%;
  cursor: pointer;
  transition: background 150ms, box-shadow 150ms;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.btn-primary:hover:not(:disabled) {
  background: #5BCEFF;
  box-shadow: 0 0 20px rgba(58, 190, 255, 0.30);
}

.btn-primary:disabled {
  background: var(--color-bg-panel-raised);
  color: var(--color-text-muted);
  cursor: not-allowed;
  box-shadow: none;
}

.btn-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(11, 18, 32, 0.3);
  border-top-color: #0B1220;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.action-hint {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  text-align: center;
  margin-top: 8px;
}
</style>
