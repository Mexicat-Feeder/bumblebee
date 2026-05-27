import { writable, derived } from 'svelte/store';

export type PipelinePhase = 'idle' | 'creating' | 'coding' | 'qa' | 'done';

export interface PipelineState {
  phase: PipelinePhase;
  /** Tickets created so far (from decompose SSE stream) */
  createdTickets: number;
  /** Total tickets (set when decompose finishes) */
  totalTickets: number;
  /** Tickets still in coding queue (pending + in_progress) */
  codingRemaining: number;
  /** Currently building ticket ID */
  codingCurrentId: string;
  /** Currently building ticket description (first line) */
  codingCurrentDesc: string;
  /** Tickets that passed QA */
  qaVerified: number;
  /** Tickets that failed / are blocked */
  qaFailed: number;
  /** Is executor running? */
  executorRunning: boolean;
  /** Cloud cost for decomposition (approx) */
  decompCost: number;
  /** Elapsed time in seconds */
  elapsedSeconds: number;
  /** Error message if any */
  error: string | null;
}

const INITIAL: PipelineState = {
  phase: 'idle',
  createdTickets: 0,
  totalTickets: 0,
  codingRemaining: 0,
  codingCurrentId: '',
  codingCurrentDesc: '',
  qaVerified: 0,
  qaFailed: 0,
  executorRunning: false,
  decompCost: 0,
  elapsedSeconds: 0,
  error: null,
};

function createPipelineStore() {
  const { subscribe, set, update } = writable<PipelineState>({ ...INITIAL });
  let elapsedTimer: ReturnType<typeof setInterval> | null = null;
  let statusPoller: ReturnType<typeof setInterval> | null = null;

  function reset() {
    stopTimers();
    set({ ...INITIAL });
  }

  function stopTimers() {
    if (elapsedTimer) { clearInterval(elapsedTimer); elapsedTimer = null; }
    if (statusPoller) { clearInterval(statusPoller); statusPoller = null; }
  }

  function startElapsedTimer() {
    if (elapsedTimer) return;
    elapsedTimer = setInterval(() => {
      update(s => ({ ...s, elapsedSeconds: s.elapsedSeconds + 1 }));
    }, 1000);
  }

  /** Signal decomposition has started (DecompReview handles the actual SSE) */
  function startDecompose() {
    reset();
    update(s => ({ ...s, phase: 'creating' }));
    startElapsedTimer();
  }

  /** Called by DecompReview as each ticket arrives from SSE */
  function ticketCreated() {
    update(s => ({
      ...s,
      createdTickets: s.createdTickets + 1,
    }));
  }

  /** Called when decomposition plan is complete */
  function decompComplete(totalTickets: number) {
    update(s => ({
      ...s,
      totalTickets: totalTickets || s.createdTickets,
      decompCost: 0.03,
    }));
  }

  /** Called when decomposition fails */
  function decompError(message: string) {
    update(s => ({ ...s, error: message }));
  }

  /** Transition to coding phase — starts polling executor status */
  function startCoding(slug: string) {
    update(s => ({ ...s, phase: 'coding' }));
    startElapsedTimer();
    pollExecutorStatus(slug);
    statusPoller = setInterval(() => pollExecutorStatus(slug), 3000);
  }

  async function pollExecutorStatus(slug: string) {
    try {
      const resp = await fetch(`/api/projects/${slug}/executor/status`);
      if (!resp.ok) return;
      const data = await resp.json();
      const stats: Record<string, number> = data.ticket_stats ?? {};

      const pending = (stats['pending'] ?? 0);
      const inProgress = (stats['in_progress'] ?? 0);
      const done = (stats['done'] ?? 0);
      const qaVerified = (stats['qa_verified'] ?? 0);
      const blocked = (stats['blocked'] ?? 0);
      const codingRemaining = pending + inProgress;

      update(s => ({
        ...s,
        executorRunning: data.running ?? false,
        codingRemaining,
        qaVerified,
        qaFailed: blocked,
        totalTickets: s.totalTickets || Object.values(stats).reduce((a: number, b: number) => a + b, 0),
      }));

      // Auto-transition to QA phase when coding is done
      if (!data.running && codingRemaining === 0 && (done + qaVerified + blocked) > 0) {
        update(s => {
          if (s.phase === 'coding') {
            return { ...s, phase: 'qa' };
          }
          return s;
        });
      }
    } catch { /* ignore */ }
  }

  /** Update from ticket SSE stream (existing ticketStore) */
  function updateFromTickets(tickets: Array<{ status: string; id: string }>) {
    const stats: Record<string, number> = {};
    for (const t of tickets) {
      stats[t.status] = (stats[t.status] ?? 0) + 1;
    }

    const pending = stats['pending'] ?? 0;
    const inProgress = stats['in_progress'] ?? 0;
    const qaVerified = stats['qa_verified'] ?? 0;
    const blocked = stats['blocked'] ?? 0;

    const currentTicket = tickets.find(t => t.status === 'in_progress');

    update(s => ({
      ...s,
      codingRemaining: pending + inProgress,
      qaVerified,
      qaFailed: blocked,
      codingCurrentId: currentTicket?.id ?? '',
      totalTickets: s.totalTickets || tickets.length,
    }));
  }

  function markDone() {
    stopTimers();
    update(s => ({ ...s, phase: 'done' }));
  }

  return {
    subscribe,
    reset,
    startDecompose,
    ticketCreated,
    decompComplete,
    decompError,
    startCoding,
    updateFromTickets,
    markDone,
    stopTimers,
  };
}

export const pipelineStore = createPipelineStore();

// Derived convenience stores
export const pipelinePhase = derived(pipelineStore, s => s.phase);
export const pipelineCreated = derived(pipelineStore, s => s.createdTickets);
export const pipelineCodingRemaining = derived(pipelineStore, s => s.codingRemaining);
export const pipelineQAVerified = derived(pipelineStore, s => s.qaVerified);
