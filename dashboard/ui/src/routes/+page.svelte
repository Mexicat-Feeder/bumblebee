<script lang="ts">
  import { onMount } from 'svelte';
  import { ticketStore } from '$lib/stores/tickets';
  import { telemetry } from '$lib/stores/telemetry';
  import { projectsStore, selectedProject, activeView } from '$lib/stores/projects';
  import PipelineView from '$lib/components/PipelineView.svelte';
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
{:else if $activeView === 'costs' && $selectedProject}
  <CostComparison slug={$selectedProject.slug} />
{:else}
  <!-- Pipeline view — main dashboard content -->
  <PipelineView
    slug={$selectedProject?.slug ?? ''}
    projectName={$selectedProject?.name ?? 'Agent Swarm'}
    projectStatus={$selectedProject?.status ?? ''}
  />
{/if}
