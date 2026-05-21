import { writable } from 'svelte/store';

interface HardwareMetrics {
  cpu_percent: number | null;
  ram_used_gb: number | null;
  ram_total_gb: number | null;
  igpu_mem_gb: number | null;
  gpu_3d_percent: number | null;
}

interface InferenceMetrics {
  tokens_per_second: number | null;
  time_to_first_token: number | null;
  npu_utilization: number | null;
}

interface TelemetryState {
  hardware: HardwareMetrics;
  inference: InferenceMetrics;
}

function createTelemetryStore() {
  const { subscribe, set } = writable<TelemetryState>({
    hardware: {
      cpu_percent: null,
      ram_used_gb: null,
      ram_total_gb: null,
      igpu_mem_gb: null,
      gpu_3d_percent: null,
    },
    inference: {
      tokens_per_second: null,
      time_to_first_token: null,
      npu_utilization: null,
    },
  });

  let interval: ReturnType<typeof setInterval> | null = null;

  async function poll() {
    const hw = await fetch('/api/telemetry/hardware')
      .then((r) => r.json())
      .catch(() => null);
    const inf = await fetch('/api/telemetry/speed')
      .then((r) => r.json())
      .catch(() => null);
    set({
      hardware:
        hw || {
          cpu_percent: null,
          ram_used_gb: null,
          ram_total_gb: null,
          igpu_mem_gb: null,
          gpu_3d_percent: null,
        },
      inference:
        inf || {
          tokens_per_second: null,
          time_to_first_token: null,
          npu_utilization: null,
        },
    });
  }

  function start() {
    poll();
    interval = setInterval(poll, 2000);
  }

  function stop() {
    if (interval) clearInterval(interval);
  }

  return { subscribe, start, stop };
}

export const telemetry = createTelemetryStore();
