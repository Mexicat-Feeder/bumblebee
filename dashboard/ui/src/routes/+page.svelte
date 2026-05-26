<script lang="ts">
  import { onMount } from 'svelte';
  import { ticketStore } from '$lib/stores/tickets';
  import { telemetry } from '$lib/stores/telemetry';
  import { projectsStore, selectedProject, activeView } from '$lib/stores/projects';
  import KpiBoard from '$lib/components/KpiBoard.svelte';
  import GateProgress from '$lib/components/GateProgress.svelte';
  import PixelActivity from '$lib/components/PixelActivity.svelte';
  import HardwarePanel from '$lib/components/HardwarePanel.svelte';
  import LocalAIPanel from '$lib/components/LocalAIPanel.svelte';
  import DispatchTable from '$lib/components/DispatchTable.svelte';
  import LemonadeLog from '$lib/components/LemonadeLog.svelte';
  import IntakeView from '$lib/components/IntakeView.svelte';
  import ResearchIntakeView from '$lib/components/ResearchIntakeView.svelte';
  import ResearchReportView from '$lib/components/ResearchReportView.svelte';
  import CostComparison from '$lib/components/CostComparison.svelte';
  import { selectedResearchId, researchView } from '$lib/stores/research';

  // Connect ticket store to the selected project's DB
  let connectedSlug = '';
  $: currentSlug = $selectedProject?.slug ?? 'dashboard';
  $: if (currentSlug !== connectedSlug) {
    connectedSlug = currentSlug;
    ticketStore.connect(currentSlug);
  }

  onMount(() => {
    telemetry.start();
    return () => {
      ticketStore.disconnect();
      telemetry.stop();
    };
  });
</script>

{#if $selectedResearchId !== null}
  {#if $researchView === 'report'}
    <ResearchReportView ticketId={$selectedResearchId} />
  {:else}
    <ResearchIntakeView />
  {/if}
{:else if !$selectedResearchId && $researchView === 'intake' && !$selectedProject && $activeView !== 'intake'}
  <ResearchIntakeView />
{:else if $activeView === 'intake' || (!$selectedProject && $activeView === 'intake')}
  <IntakeView />
{:else if $activeView === 'costs' && $selectedProject}
  <CostComparison slug={$selectedProject.slug} />
{:else}
  <div class="dashboard">
    <!-- Row 1: KPI Cards -->
    <KpiBoard projectName={$selectedProject?.name ?? 'Agent Swarm Dashboard'} />

    <!-- Row 2: Gate Progress -->
    <section class="gate-progress-row">
      <GateProgress manualGates={currentSlug === 'dashboard-s2' ? {
        4: 'complete',
        5: 'active',
        6: 'pending'
      } : {}} />
    </section>

    <!-- Row 3: Pixel Activity + Hardware + Local AI -->
    <section class="three-col-row">
      <div class="panel pixel-panel">
        <PixelActivity />
      </div>
      <div class="panel hw-panel">
        <HardwarePanel />
      </div>
      <div class="panel local-ai-panel">
        <LocalAIPanel />
      </div>
    </section>

    <!-- Row 4: Dispatch Table | Lemonade Log -->
    <section class="bottom-row">
      <div class="panel bottom-left">
        <DispatchTable />
      </div>
      <div class="panel bottom-right">
        <LemonadeLog />
      </div>
    </section>
  </div>
{/if}

<style>
  .dashboard {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-panel-gap);
    width: 100%;
  }

  .panel {
    background: var(--color-bg-panel);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: var(--radius-panel);
    box-shadow: 0 4px 32px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.04);
    padding: var(--spacing-panel-pad);
  }

  .gate-progress-row {
    display: grid;
    grid-template-columns: 1fr;
  }

  .three-col-row {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: var(--spacing-row-gap);
  }

  .pixel-panel,
  .hw-panel,
  .local-ai-panel {
    min-height: 200px;
  }

  .bottom-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--spacing-row-gap);
  }

  .bottom-left,
  .bottom-right {
    min-height: 200px;
  }

  @media (max-width: 1100px) {
    .three-col-row {
      grid-template-columns: 1fr 1fr;
    }
  }

  @media (max-width: 768px) {
    .three-col-row,
    .bottom-row {
      grid-template-columns: 1fr;
    }
  }
</style>
