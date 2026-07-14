/**
 * Global UI state store (Zustand).
 *
 * Stores only client-side UI state — sidebar collapse, mobile menu,
 * active modal, page title. No server state lives here (that belongs
 * in TanStack Query).
 *
 * Persistence: sidebar collapse preference is saved to localStorage
 * so it survives page refreshes.
 */

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type ModalKey =
  | "create-project"
  | "delete-project"
  | "create-video"
  | "delete-video"
  | "settings"
  | null;

interface UIState {
  // ---- Sidebar ----
  sidebarCollapsed: boolean;
  mobileMenuOpen: boolean;

  // ---- Page context ----
  pageTitle: string;
  pageBreadcrumbs: { label: string; href?: string }[];

  // ---- Modals ----
  activeModal: ModalKey;
  activeItemId: string | null;
}

interface UIActions {
  // ---- Sidebar ----
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setMobileMenuOpen: (open: boolean) => void;
  closeMobileMenu: () => void;

  // ---- Page context ----
  setPageTitle: (title: string) => void;
  setPageBreadcrumbs: (crumbs: { label: string; href?: string }[]) => void;

  // ---- Modals ----
  openModal: (key: ModalKey, itemId?: string) => void;
  closeModal: () => void;
}

type UIStore = UIState & UIActions;

// ---------------------------------------------------------------------------
// Store
// ---------------------------------------------------------------------------

export const useUIStore = create<UIStore>()(
  persist(
    (set) => ({
      // ---- Initial state ----
      sidebarCollapsed: false,
      mobileMenuOpen: false,
      pageTitle: "Dashboard",
      pageBreadcrumbs: [],
      activeModal: null,
      activeItemId: null,

      // ---- Sidebar actions ----
      toggleSidebar: () =>
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),

      setSidebarCollapsed: (collapsed) =>
        set({ sidebarCollapsed: collapsed }),

      setMobileMenuOpen: (open) =>
        set({ mobileMenuOpen: open }),

      closeMobileMenu: () =>
        set({ mobileMenuOpen: false }),

      // ---- Page context actions ----
      setPageTitle: (title) =>
        set({ pageTitle: title }),

      setPageBreadcrumbs: (crumbs) =>
        set({ pageBreadcrumbs: crumbs }),

      // ---- Modal actions ----
      openModal: (key, itemId = null) =>
        set({ activeModal: key, activeItemId: itemId }),

      closeModal: () =>
        set({ activeModal: null, activeItemId: null }),
    }),
    {
      name: "prabhu-ui-state",
      storage: createJSONStorage(() => localStorage),
      // Only persist sidebar preference — everything else resets on reload
      partialState: (state: UIState) => ({
        sidebarCollapsed: state.sidebarCollapsed,
      }),
    } as Parameters<typeof persist>[1]
  )
);

// ---------------------------------------------------------------------------
// Convenience selectors
// ---------------------------------------------------------------------------

export const selectSidebarCollapsed = (s: UIStore) => s.sidebarCollapsed;
export const selectMobileMenuOpen = (s: UIStore) => s.mobileMenuOpen;
export const selectPageTitle = (s: UIStore) => s.pageTitle;
export const selectActiveModal = (s: UIStore) => s.activeModal;
