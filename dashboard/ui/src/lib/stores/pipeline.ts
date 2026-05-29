import { writable, derived } from 'svelte/store';

export type PipelinePhase = 'idle' | 'creating' | 'committing' | 'coding' | 'integrating' | 'done';

export interface PipelineTicket {
  id: string;
  gate: number;
  description: string;
  required_output_files: string[];
  depends_on: string[];
  is_parent: boolean;
}

export interface PipelineState {
  phase: PipelinePhase;
  /** Tickets created so far (from decompose SSE stream) */
  createdTickets: number;
  /** Total tickets (set when decompose finishes) */
  totalTickets: number;
  /** Actual ticket objects from decomposition */
  tickets: PipelineTicket[];
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
  tickets: [],
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
    update(s => ({ ...s, phase: 'creating', tickets: [] }));
    startElapsedTimer();
  }

  /** Called by DecompReview as each ticket arrives from SSE */
  function ticketCreated(ticket?: PipelineTicket) {
    update(s => ({
      ...s,
      createdTickets: s.createdTickets + 1,
      tickets: ticket ? [...s.tickets, ticket] : s.tickets,
    }));
  }

  /** Called when decomposition plan is complete — auto-commits and starts executor */
  function decompComplete(totalTickets: number, slug?: string) {
    update(s => ({
      ...s,
      totalTickets: totalTickets || s.createdTickets,
      decompCost: 0.03,
      phase: 'committing',
    }));
    if (slug) {
      autoCommitAndBuild(slug);
    }
  }

  /** Auto-commit the plan, then start the executor */
  async function autoCommitAndBuild(slug: string) {
    try {
      // Commit plan to DB
      const commitResp = await fetch(`/api/projects/${slug}/decompose/commit`, {
        method: 'POST',
      });
      if (!commitResp.ok) {
        const data = await commitResp.json().catch(() => ({ detail: commitResp.statusText }));
        throw new Error(`Commit failed: ${data.detail || commitResp.status}`);
      }

      // Start the executor
      const startResp = await fetch(`/api/projects/${slug}/executor/start`, {
        method: 'POST',
      });
      if (!startResp.ok) {
        const data = await startResp.json().catch(() => ({ detail: startResp.statusText }));
        throw new Error(`Executor start failed: ${data.detail || startResp.status}`);
      }

      // Transition to coding
      startCoding(slug);
    } catch (e: any) {
      update(s => ({ ...s, error: e.message || 'Failed to start build', phase: 'creating' }));
    }
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
        createdTickets: s.createdTickets || Object.values(stats).reduce((a: number, b: number) => a + b, 0),
      }));

      // Auto-transition phases
      const totalDone = done + qaVerified + blocked;
      if (!data.running && codingRemaining === 0 && totalDone > 0) {
        update(s => {
          if (s.phase === 'coding') {
            return { ...s, phase: 'integrating' };
          }
          // All verified (or verified + blocked) and executor stopped → done
          if (s.phase === 'integrating' && qaVerified > 0 && codingRemaining === 0 && (done === 0 || done + qaVerified + blocked === s.totalTickets)) {
            stopTimers();
            return { ...s, phase: 'done' };
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
