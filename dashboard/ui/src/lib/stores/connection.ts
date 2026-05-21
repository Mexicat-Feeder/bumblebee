import { writable } from 'svelte/store';

interface ServiceStatus {
  name: string;
  ok: boolean;
  detail: string;
}

interface ConnectionState {
  reachable: boolean;
  healthy: boolean;
  services: ServiceStatus[];
  lastCheck: Date | null;
}

function createConnectionStore() {
  const { subscribe, set } = writable<ConnectionState>({
    reachable: true,
    healthy: true,
    services: [],
    lastCheck: null
  });

  let interval: ReturnType<typeof setInterval> | null = null;

  async function check() {
    try {
      const resp = await fetch('/api/health');
      const data = await resp.json();
      set({
        reachable: true,
        healthy: data.ok === true,
        services: data.services || [],
        lastCheck: new Date()
      });
    } catch {
      set({
        reachable: false,
        healthy: false,
        services: [],
        lastCheck: new Date()
      });
    }
  }

  function start() {
    check();
    interval = setInterval(check, 5000);
  }

  function stop() {
    if (interval) clearInterval(interval);
  }

  return { subscribe, start, stop };
}

export const connection = createConnectionStore();
