import { writable } from 'svelte/store';

export interface CostData {
  project_name: string;
  slug: string;
  total_tickets: number;
  completed_tickets: number;
  total_duration_s: number;
  total_tool_calls: number;
  total_files_written: number;
  artifact_count: number;
  estimated_input_tokens: number;
  estimated_output_tokens: number;
  cloud_costs: Record<string, number>;
  local_cost: number;
  pricing: Record<string, { input: number; output: number; label: string }>;
}

export const costData = writable<CostData | null>(null);
export const costLoading = writable(true);
export const costError = writable<string | null>(null);

let interval: ReturnType<typeof setInterval> | null = null;
let currentSlug: string | null = null;

export async function fetchCosts(slug: string) {
  costLoading.set(true);
  costError.set(null);
  currentSlug = slug;
  try {
    const res = await fetch(`/api/costs/${slug}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data: CostData = await res.json();
    costData.set(data);
  } catch (e: any) {
    costError.set(e.message ?? 'Failed to load cost data');
  } finally {
    costLoading.set(false);
  }
}

export function startCostPolling(slug: string) {
  stopCostPolling();
  fetchCosts(slug);
  interval = setInterval(() => fetchCosts(slug), 30000);
}

export function stopCostPolling() {
  if (interval) {
    clearInterval(interval);
    interval = null;
  }
  currentSlug = null;
}
