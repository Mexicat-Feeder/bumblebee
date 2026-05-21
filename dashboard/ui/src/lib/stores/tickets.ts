import { writable, derived } from 'svelte/store';

export interface Ticket {
  id: string;
  status: string;
  gate: number;
  assignee: string | null;
  parent_ticket_id: string | null;
  updated_at: string;
  failure_count: number;
  blocked_reason_code: string | null;
}

interface TicketState {
  tickets: Ticket[];
  loading: boolean;
  error: string | null;
}

function createTicketStore() {
  const { subscribe, set, update } = writable<TicketState>({
    tickets: [], loading: true, error: null
  });
  let eventSource: EventSource | null = null;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  function connect(slug: string) {
    disconnect();
    set({ tickets: [], loading: true, error: null });
    eventSource = new EventSource(`/api/tickets/${slug}/stream`);
    eventSource.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.type === 'snapshot') {
          set({ tickets: data.tickets, loading: false, error: null });
        } else if (data.type === 'update') {
          update(state => {
            const updated = new Map(state.tickets.map(t => [t.id, t]));
            for (const t of data.tickets) updated.set(t.id, t);
            return { ...state, tickets: Array.from(updated.values()) };
          });
        }
      } catch { /* ignore parse errors */ }
    };
    eventSource.onerror = () => {
      eventSource?.close();
      update(s => ({ ...s, error: 'Connection lost' }));
      reconnectTimer = setTimeout(() => connect(slug), 5000);
    };
  }

  function disconnect() {
    eventSource?.close();
    eventSource = null;
    if (reconnectTimer) clearTimeout(reconnectTimer);
  }

  return { subscribe, connect, disconnect };
}

export const ticketStore = createTicketStore();

export const totalScope = derived(ticketStore, ($s) =>
  $s.tickets.length
);
export const completionPct = derived(ticketStore, ($s) => {
  const all = $s.tickets;
  if (all.length === 0) return 0;
  const verified = all.filter((t) => t.status === 'qa_verified').length;
  return Math.round((verified / all.length) * 100);
});
export const blockedCount = derived(ticketStore, ($s) =>
  $s.tickets.filter((t) => t.status === 'blocked').length
);
export const blockedTickets = derived(ticketStore, ($s) =>
  $s.tickets.filter((t) => t.status === 'blocked')
);
export const activeTicket = derived(ticketStore, ($s) => {
  const inProgress = $s.tickets
    .filter(t => t.status === 'in_progress')
    .sort((a, b) => b.updated_at.localeCompare(a.updated_at));
  if (inProgress.length > 0) return inProgress[0];
  const recent = $s.tickets
    .filter(t => ['done', 'qa_verified'].includes(t.status))
    .sort((a, b) => b.updated_at.localeCompare(a.updated_at));
  return recent[0] ?? null;
});
