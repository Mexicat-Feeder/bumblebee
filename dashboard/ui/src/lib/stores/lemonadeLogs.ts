import { writable } from 'svelte/store';

interface LogState {
  lines: string[];
  connected: boolean;
}

const MAX_LINES = 200;

function createLogStore() {
  const { subscribe, update } = writable<LogState>({ lines: [], connected: false });
  let es: EventSource | null = null;

  function connect() {
    es = new EventSource('/api/logs/lemonade/stream');
    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        update(state => ({
          lines: [...state.lines, data.line].slice(-MAX_LINES),
          connected: true
        }));
      } catch { /* ignore */ }
    };
    es.onerror = () => {
      es?.close();
      update(s => ({ ...s, connected: false }));
      setTimeout(connect, 5000);
    };
  }

  function disconnect() {
    es?.close();
    es = null;
  }

  return { subscribe, connect, disconnect };
}

export const lemonadeLogStore = createLogStore();
