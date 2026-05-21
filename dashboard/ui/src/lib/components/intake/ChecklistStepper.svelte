<script lang="ts">
  export let checklist: {
    named: boolean;
    prd_uploaded: boolean;
    refs_uploaded: boolean;
    qa_complete: boolean;
    approved: boolean;
    scaffolded: boolean;
    running: boolean;
  } = {
    named: false,
    prd_uploaded: false,
    refs_uploaded: false,
    qa_complete: false,
    approved: false,
    scaffolded: false,
    running: false
  };
  
  export let status: string = 'intake';  // project status for in-progress detection
  
  interface Step {
    key: string;
    label: string;
    state: 'complete' | 'active' | 'pending';
  }
  
  $: steps = computeSteps(checklist, status);
  
  function computeSteps(cl: typeof checklist, st: string): Step[] {
    return [
      { key: 'named', label: 'Named', state: cl.named ? 'complete' : 'pending' },
      { key: 'prd', label: 'PRD', state: cl.prd_uploaded ? 'complete' : 'pending' },
      { key: 'qa', label: 'Q&A', state: cl.qa_complete ? 'complete' : (st === 'qa_pending' ? 'active' : 'pending') },
      { key: 'approved', label: 'Approved', state: cl.approved ? 'complete' : 'pending' },
      { key: 'built', label: 'Built', state: cl.scaffolded || cl.running ? 'complete' : 'pending' },
    ];
  }
</script>

<div class="stepper">
  {#each steps as step, i}
    <div class="step" class:step--complete={step.state === 'complete'} class:step--active={step.state === 'active'}>
      <div class="step-icon">
        {#if step.state === 'complete'}
          <span class="icon-check">✓</span>
        {:else if step.state === 'active'}
          <span class="icon-pulse"></span>
        {:else}
          <span class="icon-empty"></span>
        {/if}
      </div>
      <span class="step-label">{step.label}</span>
    </div>
    {#if i < steps.length - 1}
      <div class="step-connector" class:step-connector--complete={step.state === 'complete'}></div>
    {/if}
  {/each}
</div>

<style>
  .stepper {
    display: flex;
    align-items: center;
    gap: 0;
    padding: 16px 0;
  }

  .step {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    min-width: 60px;
  }

  .step-icon {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px solid var(--color-text-muted);
    background: transparent;
    transition: border-color 300ms, background 300ms;
  }

  .step--complete .step-icon {
    border-color: var(--color-accent-complete);
    background: rgba(45, 230, 230, 0.15);
  }

  .step--active .step-icon {
    border-color: var(--color-accent-primary);
    background: rgba(58, 190, 255, 0.10);
  }

  .icon-check {
    color: var(--color-accent-complete);
    font-size: 0.85rem;
    font-weight: 700;
  }

  .icon-pulse {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--color-accent-primary);
    animation: pulse 2s ease-in-out infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 0.4; }
    50% { opacity: 1; }
  }

  .icon-empty {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--color-text-muted);
  }

  .step-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--color-text-muted);
  }

  .step--complete .step-label {
    color: var(--color-accent-complete);
  }

  .step--active .step-label {
    color: var(--color-accent-primary);
  }

  .step-connector {
    flex: 1;
    height: 2px;
    background: var(--color-text-muted);
    min-width: 20px;
    margin-bottom: 20px;  /* align with icon center, not label */
  }

  .step-connector--complete {
    background: var(--color-accent-complete);
  }

  @media (max-width: 500px) {
    .stepper {
      flex-direction: column;
      align-items: flex-start;
      gap: 8px;
    }
    .step {
      flex-direction: row;
      gap: 10px;
    }
    .step-connector {
      display: none;
    }
  }
</style>
