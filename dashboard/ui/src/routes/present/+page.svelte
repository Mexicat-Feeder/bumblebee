<script lang="ts">
  import { onMount } from 'svelte';
  import { ticketStore } from '$lib/stores/tickets';
  import { telemetry } from '$lib/stores/telemetry';
  import PresentationMode from '$lib/components/PresentationMode.svelte';

  onMount(() => {
    ticketStore.connect('dashboard');
    telemetry.start();
    return () => { ticketStore.disconnect(); telemetry.stop(); };
  });
</script>

<PresentationMode />

<style>
  :global(body) { overflow: hidden; }
</style>
