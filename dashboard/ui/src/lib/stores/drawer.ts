import { writable, derived } from 'svelte/store';
import { projectsStore } from '$lib/stores/projects';

export type DrawerMode = 'closed' | 'forge' | 'sift';

export const drawerMode = writable<DrawerMode>('closed');

export const drawerOpen = derived(drawerMode, m => m !== 'closed');

// Right-side ticket details drawer
export const ticketDrawerOpen = writable<boolean>(false);

export function openTicketDrawer() {
  ticketDrawerOpen.set(true);
  reportDrawerOpen.set(false);
}

export function closeTicketDrawer() {
  ticketDrawerOpen.set(false);
}

// Right-side coding log drawer
export const codingDrawerOpen = writable<boolean>(false);

export function openCodingDrawer() {
  codingDrawerOpen.set(true);
  ticketDrawerOpen.set(false);
  reportDrawerOpen.set(false);
}

export function closeCodingDrawer() {
  codingDrawerOpen.set(false);
}

// Right-side research report drawer
export const reportDrawerOpen = writable<boolean>(false);

export function openReportDrawer() {
  reportDrawerOpen.set(true);
  ticketDrawerOpen.set(false);
}

export function closeReportDrawer() {
  reportDrawerOpen.set(false);
}

export function openForgeDrawer() {
  // Deselect project so the form starts blank
  projectsStore.selectProject(null, 'intake');
  drawerMode.set('forge');
}

export function openSiftDrawer() {
  drawerMode.set('sift');
}

export function openDrawer() {
  openForgeDrawer();
}

export function closeDrawer() {
  drawerMode.set('closed');
}
