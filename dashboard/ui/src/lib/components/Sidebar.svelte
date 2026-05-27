<script lang="ts">
  import { projectsStore, selectedProject, activeView } from '$lib/stores/projects';
  import { researchStore, selectedResearchId, researchView, selectResearch, newResearch, researchStatusColor, researchStatusLabel } from '$lib/stores/research';
  import { openDrawer } from '$lib/stores/drawer';
  
  let expandedSlug: string | null = null;
  
  function toggleExpand(slug: string) {
    expandedSlug = expandedSlug === slug ? null : slug;
  }
  
  function selectView(slug: string, view: 'intake' | 'dashboard' | 'costs') {
    projectsStore.selectProject(slug, view);
    expandedSlug = slug;
    selectedResearchId.set(null);
  }
  
  function newProject() {
    projectsStore.selectProject(null, 'intake');
    selectedResearchId.set(null);
    openDrawer();
  }

  function openNewResearch() {
    newResearch();
    projectsStore.selectProject(null, null);
  }

  function openResearch(id: string, view: 'intake' | 'report') {
    selectResearch(id, view);
    projectsStore.selectProject(null, null);
  }

  $: activeResearchId = $selectedResearchId;
  
  // Blue  = pre-build (intake / QA phases)
  // Yellow = building (scaffolded, no blocked)
  // Green  = live (running)
  // Red    = has blocked tickets (any status)
  function getStatusColor(status: string, blockedCount: number = 0): string {
    if (blockedCount > 0) return '#ff6b6b';
    if (status === 'running') return '#63d38f';
    if (status === 'scaffolded') return '#ffd166';
    // intake, qa_pending, qa_complete, approved
    return 'var(--color-accent-primary)';
  }

  function getStatusLabel(status: string, blockedCount: number = 0): string {
    if (blockedCount > 0) return `blocked (${blockedCount} ticket${blockedCount !== 1 ? 's' : ''})`;
    const labels: Record<string, string> = {
      intake: 'intake',
      qa_pending: 'Q\u0026A in progress',
      qa_complete: 'Q\u0026A complete',
      approved: 'approved',
      scaffolded: 'building',
      running: 'live',
    };
    return labels[status] ?? status;
  }
  
  function isDashboardDisabled(status: string): boolean {
    return status === 'intake' || status === 'qa_pending';
  }
  
  function isActive(slug: string, view: string): boolean {
    return $selectedProject?.slug === slug && $activeView === view;
  }
</script>

<div class="sidebar">
  <!-- Logo area -->
  <div class="sidebar-header">
    <span class="logo-icon">◆</span>
    <span class="logo-text">Agent Swarm</span>
  </div>

  <!-- New Project button -->
  <button class="new-project-btn" on:click={newProject}>
    <span class="btn-icon">➕</span>
    <span class="btn-label">New Project</span>
  </button>

  <!-- Loading state -->
  {#if $projectsStore.loading}
    <div class="loading-indicator">
      <span class="loading-dot"></span>
      <span class="loading-dot"></span>
      <span class="loading-dot"></span>
      <span class="loading-text">Loading...</span>
    </div>
  {:else if $projectsStore.error}
    <div class="error-message">
      ⚠ {$projectsStore.error}
    </div>
  {:else if $projectsStore.projects.length === 0}
    <div class="empty-state">No projects yet</div>
  {:else}
    <!-- Project list -->
    <div class="project-list">
      {#each $projectsStore.projects as project (project.slug)}
        <div class="project-group">
          <!-- Project name row -->
          <div
            class="project-row"
            on:click={() => toggleExpand(project.slug)}
          >
            <span
              class="status-dot"
              style="background-color: {getStatusColor(project.status, project.blocked_count ?? 0)}"
              title={getStatusLabel(project.status, project.blocked_count ?? 0)}
            ></span>
            <span class="project-name">{project.name}</span>
            <span class="expand-icon">
              {expandedSlug === project.slug ? '▼' : '▶'}
            </span>
          </div>

          <!-- Sub-items -->
          {#if expandedSlug === project.slug}
            <div class="sub-items">
              <button
                class="sub-link intake-link"
                on:click={() => selectView(project.slug, 'intake')}
                class:active={$selectedProject?.slug === project.slug && $activeView === 'intake'}
              >
                📋 Intake
              </button>
              <button
                class="sub-link dashboard-link"
                on:click={() => !isDashboardDisabled(project.status) && selectView(project.slug, 'dashboard')}
                class:disabled={isDashboardDisabled(project.status)}
                class:active={$selectedProject?.slug === project.slug && $activeView === 'dashboard'}
                title={isDashboardDisabled(project.status) ? 'Available after Q&A completes' : ''}
              >
                📊 Dashboard
              </button>
              <button
                class="sub-link costs-link"
                on:click={() => !isDashboardDisabled(project.status) && selectView(project.slug, 'costs')}
                class:disabled={isDashboardDisabled(project.status)}
                class:active={$selectedProject?.slug === project.slug && $activeView === 'costs'}
                title="Cloud vs Local cost comparison"
              >
                💰 Cost Comparison
              </button>
            </div>
          {/if}
        </div>
      {/each}
    </div>
  {/if}

  <!-- Research section -->
  <div class="section-divider">
    <span class="section-label">Research</span>
    <button class="section-add" on:click={openNewResearch} title="New research request">＋</button>
  </div>

  {#if $researchStore.loading}
    <div class="research-loading">Loading…</div>
  {:else if $researchStore.tickets.length === 0}
    <div class="research-empty">No research tickets yet</div>
  {:else}
    <div class="research-list">
      {#each $researchStore.tickets as ticket (ticket.id)}
        <div
          class="research-row"
          class:active={activeResearchId === ticket.id}
          on:click={() => openResearch(ticket.id, ticket.display_status === 'complete' ? 'report' : 'report')}
        >
          <span
            class="status-square"
            style="background-color: {researchStatusColor(ticket.display_status)}"
            title={researchStatusLabel(ticket.display_status, ticket.queue_status)}
          ></span>
          <span class="research-id">{ticket.id}</span>
          <span class="research-desc">{(ticket.ticket_description ?? '').split('\n')[0].slice(0, 40)}{(ticket.ticket_description ?? '').length > 40 ? '…' : ''}</span>
        </div>
      {/each}
    </div>
  {/if}

  <!-- Error at bottom if present -->
  {#if $projectsStore.error}
    <div class="error-footer">
      ⚠ {$projectsStore.error}
    </div>
  {/if}
</div>

<style>
  .sidebar {
    width: 240px;
    height: 100vh;
    background-color: var(--color-bg-sidebar);
    border-right: 1px solid rgba(255, 255, 255, 0.06);
    display: flex;
    flex-direction: column;
    font-family: var(--font-ui);
    overflow: hidden;
  }

  /* Logo area */
  .sidebar-header {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 16px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  }

  .logo-icon {
    color: var(--color-accent-primary);
    font-size: 18px;
    line-height: 1;
  }

  .logo-text {
    color: var(--color-accent-primary);
    font-size: 14px;
    font-weight: 600;
    letter-spacing: 0.5px;
  }

  /* New Project button */
  .new-project-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    width: calc(100% - 24px);
    padding: 10px 16px;
    margin: 12px 12px 0 12px;
    box-sizing: border-box;
    background: transparent;
    border: 1px solid rgba(58, 190, 255, 0.3);
    border-radius: var(--radius-badge);
    color: var(--color-text-primary);
    font-family: var(--font-ui);
    font-size: 13px;
    cursor: pointer;
    transition: background-color 0.15s ease;
  }

  .new-project-btn:hover {
    background-color: rgba(58, 190, 255, 0.08);
  }

  .btn-icon {
    font-size: 14px;
  }

  .btn-label {
    font-weight: 500;
  }

  /* Loading indicator */
  .loading-indicator {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    padding: 24px 16px;
  }

  .loading-text {
    color: var(--color-text-muted);
    font-size: 13px;
  }

  .loading-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background-color: var(--color-text-muted);
    animation: pulse 1.4s ease-in-out infinite;
  }

  .loading-dot:nth-child(2) {
    animation-delay: 0.2s;
  }

  .loading-dot:nth-child(3) {
    animation-delay: 0.4s;
  }

  @keyframes pulse {
    0%, 80%, 100% {
      opacity: 0.3;
      transform: scale(0.8);
    }
    40% {
      opacity: 1;
      transform: scale(1);
    }
  }

  /* Error message */
  .error-message {
    margin: 12px;
    padding: 10px 12px;
    background-color: rgba(255, 80, 80, 0.1);
    border: 1px solid rgba(255, 80, 80, 0.2);
    border-radius: var(--radius-badge);
    color: #ff6b6b;
    font-size: 12px;
    font-family: var(--font-ui);
  }

  /* Research section */
  .section-divider {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 14px 16px 4px;
  }

  .section-label {
    flex: 1;
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--color-text-muted);
  }

  .section-add {
    background: none;
    border: none;
    color: var(--color-text-muted);
    font-size: 14px;
    cursor: pointer;
    padding: 0 2px;
    line-height: 1;
    transition: color 0.15s;
  }

  .section-add:hover { color: var(--color-accent-primary); }

  .research-loading, .research-empty {
    padding: 8px 16px;
    font-size: 12px;
    color: var(--color-text-muted);
  }

  .research-list {
    padding: 2px 12px 8px;
    display: flex;
    flex-direction: column;
    gap: 1px;
  }

  .research-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 10px;
    border-radius: var(--radius-badge);
    cursor: pointer;
    transition: background-color 0.15s;
  }

  .research-row:hover { background: rgba(255,255,255,0.04); }
  .research-row.active { background: rgba(58,190,255,0.1); }
  .research-row.active .research-id { color: var(--color-accent-primary); }

  /* Square dot — same size as .status-dot but with border-radius: 2px */
  .status-square {
    width: 8px;
    height: 8px;
    border-radius: 2px;
    flex-shrink: 0;
  }

  .research-id {
    font-size: 11px;
    font-weight: 600;
    font-family: var(--font-mono);
    color: var(--color-text-muted);
    flex-shrink: 0;
  }

  .research-desc {
    flex: 1;
    font-size: 11px;
    color: var(--color-text-secondary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .error-footer {
    margin-top: auto;
    margin: 12px;
    padding: 10px 12px;
    background-color: rgba(255, 80, 80, 0.1);
    border: 1px solid rgba(255, 80, 80, 0.2);
    border-radius: var(--radius-badge);
    color: #ff6b6b;
    font-size: 12px;
    font-family: var(--font-ui);
  }

  /* Empty state */
  .empty-state {
    padding: 24px 16px;
    color: var(--color-text-muted);
    font-size: 13px;
    text-align: center;
    font-family: var(--font-ui);
  }

  /* Project list */
  .project-list {
    flex: 1;
    overflow-y: auto;
    padding: 8px 12px;
  }

  .project-list::-webkit-scrollbar {
    width: 4px;
  }

  .project-list::-webkit-scrollbar-track {
    background: transparent;
  }

  .project-list::-webkit-scrollbar-thumb {
    background-color: rgba(255, 255, 255, 0.1);
    border-radius: 2px;
  }

  /* Project group */
  .project-group {
    margin-bottom: 2px;
  }

  /* Project row */
  .project-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 10px;
    border-radius: var(--radius-badge);
    cursor: pointer;
    transition: background-color 0.15s ease;
  }

  .project-row:hover {
    background-color: rgba(255, 255, 255, 0.04);
  }

  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .project-name {
    flex: 1;
    color: var(--color-text-primary);
    font-size: 13px;
    font-weight: 500;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .expand-icon {
    color: var(--color-text-muted);
    font-size: 10px;
    flex-shrink: 0;
  }

  /* Sub-items */
  .sub-items {
    display: flex;
    flex-direction: column;
    padding: 2px 0 2px 24px;
  }

  .sub-link {
    display: flex;
    align-items: center;
    gap: 6px;
    width: 100%;
    padding: 6px 10px;
    margin: 1px 0;
    background: transparent;
    border: none;
    border-radius: var(--radius-badge);
    color: var(--color-text-secondary);
    font-family: var(--font-ui);
    font-size: 12px;
    cursor: pointer;
    text-align: left;
    transition: background-color 0.15s ease, color 0.15s ease;
  }

  .sub-link:hover:not(.disabled) {
    background-color: rgba(255, 255, 255, 0.04);
  }

  .sub-link.disabled {
    color: var(--color-text-muted);
    cursor: default;
    opacity: 0.5;
  }

  .sub-link.disabled:hover {
    background-color: transparent;
  }

  /* Active state */
  .sub-link.active {
    background-color: rgba(58, 190, 255, 0.1);
    color: var(--color-accent-primary);
    font-weight: 500;
  }

  .project-row.active {
    background-color: rgba(58, 190, 255, 0.1);
  }

  .project-row.active .project-name {
    color: var(--color-accent-primary);
  }
</style>
