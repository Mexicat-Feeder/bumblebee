import { writable, derived } from 'svelte/store';

export interface Project {
  slug: string;
  name: string;
  description: string;
  deliverable_root: string;
  target_system: string;
  status: string;  // intake | qa_pending | qa_complete | approved | scaffolded | running
  created_at: string;
  prd_path: string | null;
  ref_paths: string[];
  tech_stack: string | null;
  visual_spec_path: string | null;
  architecture_path: string | null;
  checklist: {
    named: boolean;
    prd_uploaded: boolean;
    refs_uploaded: boolean;
    qa_complete: boolean;
    approved: boolean;
    scaffolded: boolean;
    running: boolean;
  };
}

type View = 'dashboard' | 'intake' | 'costs' | null;

interface ProjectsState {
  projects: Project[];
  loading: boolean;
  error: string | null;
  selectedSlug: string | null;
  activeView: View;
}

function createProjectsStore() {
  const { subscribe, set, update } = writable<ProjectsState>({
    projects: [],
    loading: true,
    error: null,
    selectedSlug: null,
    activeView: 'dashboard'
  });

  let pollTimer: ReturnType<typeof setInterval> | null = null;

  async function fetchProjects() {
    try {
      const resp = await fetch('/api/intake/projects');
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      update(s => ({
        ...s,
        projects: data.projects || [],
        loading: false,
        error: null
      }));
    } catch (e: any) {
      update(s => ({
        ...s,
        loading: false,
        error: e.message || 'Failed to load projects'
      }));
    }
  }

  function selectProject(slug: string | null, view?: View) {
    update(s => ({
      ...s,
      selectedSlug: slug,
      activeView: view ?? (slug ? s.activeView : 'dashboard')
    }));
  }

  function setView(view: View) {
    update(s => ({ ...s, activeView: view }));
  }

  function startPolling() {
    fetchProjects();
    pollTimer = setInterval(fetchProjects, 15000);
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  }

  return { subscribe, fetchProjects, selectProject, setView, startPolling, stopPolling };
}

export const projectsStore = createProjectsStore();

export const selectedProject = derived(projectsStore, ($s) => {
  if (!$s.selectedSlug) return null;
  return $s.projects.find(p => p.slug === $s.selectedSlug) ?? null;
});

export const activeView = derived(projectsStore, ($s) => $s.activeView);
