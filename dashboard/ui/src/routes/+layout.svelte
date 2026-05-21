<script lang="ts">
  import { onMount } from 'svelte';
  import '../app.css';
  import { connection } from '$lib/stores/connection';
  import { projectsStore } from '$lib/stores/projects';
  import { researchStore } from '$lib/stores/research';
  import StatusBanner from '$lib/components/StatusBanner.svelte';
  import Sidebar from '$lib/components/Sidebar.svelte';

  onMount(() => {
    connection.start();
    projectsStore.startPolling();
    researchStore.startPolling();
    return () => {
      connection.stop();
      projectsStore.stopPolling();
      researchStore.stopPolling();
    };
  });
</script>

<div class="layout-root">
  <Sidebar />

  <main class="main-content">
    <StatusBanner />
    <slot />
  </main>
</div>

<style>
  .layout-root {
    display: flex;
    min-height: 100vh;
    width: 100%;
  }

  .main-content {
    flex: 1;
    min-width: 0;
    overflow-x: hidden;
    overflow-y: auto;
    padding: var(--spacing-panel-gap);
  }
</style>
