import { writable } from 'svelte/store';

/** Whether the intake drawer is open */
export const drawerOpen = writable(false);

export function openDrawer() {
  drawerOpen.set(true);
}

export function closeDrawer() {
  drawerOpen.set(false);
}
