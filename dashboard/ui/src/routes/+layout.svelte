<script lang="ts">
  import { onMount } from 'svelte';
  import '../app.css';
  import { connection } from '$lib/stores/connection';
  import { projectsStore, activeView } from '$lib/stores/projects';
  import { researchStore } from '$lib/stores/research';
  import { drawerOpen, closeDrawer } from '$lib/stores/drawer';
  import StatusBanner from '$lib/components/StatusBanner.svelte';
  import Sidebar from '$lib/components/Sidebar.svelte';
  import Drawer from '$lib/components/Drawer.svelte';
  import IntakeView from '$lib/components/IntakeView.svelte';

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

  // Open drawer when activeView switches to 'intake'
  $: if ($activeView === 'intake') {
    drawerOpen.set(true);
  }

  function onDrawerClose() {
    closeDrawer();
    // Switch back to dashboard view if we were in intake
    if ($activeView === 'intake') {
      projectsStore.setView('dashboard');
    }
  }
</script>

<div class="layout-root">
  <Sidebar />

  <main class="main-content">
    <StatusBanner />
    <slot />
  </main>

  <Drawer open={$drawerOpen} title="New Project" on:close={onDrawerClose}>
    <IntakeView on:decompose-started={onDrawerClose} />
  </Drawer>
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
