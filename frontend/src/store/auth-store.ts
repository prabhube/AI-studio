/**
 * Authentication state store (Zustand + persist).
 *
 * Design decisions:
 *  - Tokens are stored in localStorage via the Zustand persist middleware.
 *    This is a deliberate trade-off: HttpOnly cookies are more secure
 *    against XSS, but require a same-origin server or a cookie-forwarding
 *    proxy. Since this is a local-first app, localStorage is acceptable.
 *  - The access token is injected into every API request by api-client.ts
 *    via a request interceptor that reads from this store.
 *  - On 401 responses, the interceptor calls refreshAccessToken() which
 *    reads the refresh token from this store.
 *  - `user` is kept in the store to avoid re-fetching the profile on
 *    every render. It is updated on login, register, and profile updates.
 */

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface AuthUser {
  id: string;
  email: string;
  username: string;
  full_name: string | null;
  avatar_url: string | null;
  role: string;
  is_active: boolean;
  is_superuser: boolean;
  email_verified: boolean;
  oauth_provider: string | null;
  last_login_at: string | null;
  created_at: string;
  updated_at: string;
}

interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;        // seconds
  issuedAt: number;         // Date.now() ms when tokens were issued
}

interface AuthState {
  user: AuthUser | null;
  tokens: AuthTokens | null;
  isLoading: boolean;
}

interface AuthActions {
  setUser: (user: AuthUser) => void;
  setTokens: (tokens: AuthTokens) => void;
  clearAuth: () => void;
  setLoading: (loading: boolean) => void;
  updateAccessToken: (accessToken: string, expiresIn: number) => void;
}

type AuthStore = AuthState & AuthActions;

// ---------------------------------------------------------------------------
// Store
// ---------------------------------------------------------------------------

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      user: null,
      tokens: null,
      isLoading: false,

      setUser: (user) => set({ user }),

      setTokens: (tokens) => set({ tokens }),

      clearAuth: () => set({ user: null, tokens: null }),

      setLoading: (loading) => set({ isLoading: loading }),

      updateAccessToken: (accessToken, expiresIn) => {
        const existing = get().tokens;
        if (!existing) return;
        set({
          tokens: {
            ...existing,
            accessToken,
            expiresIn,
            issuedAt: Date.now(),
          },
        });
      },
    }),
    {
      name: "prabhu-auth",
      storage: createJSONStorage(() => localStorage),
      // Only persist tokens and user — isLoading is transient
      partialState: (state: AuthState) => ({
        user: state.user,
        tokens: state.tokens,
      }),
    } as Parameters<typeof persist>[1]
  )
);

// ---------------------------------------------------------------------------
// Selectors (use in components to avoid re-renders on unrelated state changes)
// ---------------------------------------------------------------------------

export const selectUser = (s: AuthStore) => s.user;
export const selectIsAuthenticated = (s: AuthStore) => !!s.tokens?.accessToken;
export const selectAccessToken = (s: AuthStore) => s.tokens?.accessToken ?? null;
export const selectRefreshToken = (s: AuthStore) => s.tokens?.refreshToken ?? null;
export const selectIsLoading = (s: AuthStore) => s.isLoading;
export const selectIsAdmin = (s: AuthStore) =>
  s.user?.role === "admin" || s.user?.role === "superuser";
