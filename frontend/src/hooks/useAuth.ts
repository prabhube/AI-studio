"use client";

/**
 * useAuth — the single hook for all authentication operations.
 *
 * Provides:
 *  - Reactive auth state (isAuthenticated, user, isLoading)
 *  - login(), register(), logout(), changePassword()
 *  - initializeAuth() — call once on app boot to validate stored tokens
 *  - Role helpers (isAdmin, isSuperuser)
 *
 * The hook is a thin wrapper over the Zustand auth store + auth-api.ts.
 * Components should import from here rather than the store directly.
 */

import { useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { authApi } from "@/lib/auth-api";
import { ApiError } from "@/lib/api-client";
import {
  useAuthStore,
  selectUser,
  selectIsAuthenticated,
  selectIsLoading,
  selectIsAdmin,
} from "@/store/auth-store";
import type { RegisterPayload, LoginPayload, PasswordChangePayload } from "@/lib/auth-api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface UseAuthReturn {
  // State
  user: ReturnType<typeof selectUser>;
  isAuthenticated: boolean;
  isLoading: boolean;
  isAdmin: boolean;
  isSuperuser: boolean;

  // Operations
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => Promise<void>;
  changePassword: (payload: PasswordChangePayload) => Promise<void>;
  refreshProfile: () => Promise<void>;
  loginWithGoogle: () => Promise<void>;
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useAuth(): UseAuthReturn {
  const router = useRouter();
  const store = useAuthStore();

  const user = useAuthStore(selectUser);
  const isAuthenticated = useAuthStore(selectIsAuthenticated);
  const isLoading = useAuthStore(selectIsLoading);
  const isAdmin = useAuthStore(selectIsAdmin);
  const isSuperuser = user?.role === "superuser";

  // ------------------------------------------------------------------
  // Login
  // ------------------------------------------------------------------

  const login = useCallback(
    async (payload: LoginPayload): Promise<void> => {
      store.setLoading(true);
      try {
        const tokens = await authApi.login(payload);
        store.setTokens({
          accessToken: tokens.access_token,
          refreshToken: tokens.refresh_token,
          expiresIn: tokens.expires_in,
          issuedAt: Date.now(),
        });

        // Fetch user profile now that we have a token
        const me = await authApi.getMe();
        store.setUser(me);

        toast.success("Welcome back!", { description: me.full_name ?? me.username });
        router.push("/dashboard");
      } catch (err) {
        store.clearAuth();
        throw err; // let the login form handle the display
      } finally {
        store.setLoading(false);
      }
    },
    [store, router]
  );

  // ------------------------------------------------------------------
  // Register
  // ------------------------------------------------------------------

  const register = useCallback(
    async (payload: RegisterPayload): Promise<void> => {
      store.setLoading(true);
      try {
        await authApi.register(payload);
        toast.success("Account created!", {
          description: "Please log in to continue.",
        });
        router.push("/login");
      } finally {
        store.setLoading(false);
      }
    },
    [store, router]
  );

  // ------------------------------------------------------------------
  // Logout
  // ------------------------------------------------------------------

  const logout = useCallback(async (): Promise<void> => {
    const refreshToken = store.tokens?.refreshToken ?? "";
    store.clearAuth(); // clear immediately so UI updates
    try {
      await authApi.logout(refreshToken);
    } catch {
      // Best-effort — tokens are cleared locally regardless
    }
    toast.success("Signed out successfully.");
    router.push("/login");
  }, [store, router]);

  // ------------------------------------------------------------------
  // Change password
  // ------------------------------------------------------------------

  const changePassword = useCallback(
    async (payload: PasswordChangePayload): Promise<void> => {
      await authApi.changePassword(payload);
      toast.success("Password changed. Please log in again.");
      await logout();
    },
    [logout]
  );

  // ------------------------------------------------------------------
  // Refresh profile
  // ------------------------------------------------------------------

  const refreshProfile = useCallback(async (): Promise<void> => {
    if (!isAuthenticated) return;
    try {
      const me = await authApi.getMe();
      store.setUser(me);
    } catch (err) {
      if (err instanceof ApiError && err.isUnauthorized) {
        store.clearAuth();
        router.push("/login?session_expired=1");
      }
    }
  }, [isAuthenticated, store, router]);

  // ------------------------------------------------------------------
  // Google OAuth
  // ------------------------------------------------------------------

  const loginWithGoogle = useCallback(async (): Promise<void> => {
    try {
      const { url } = await authApi.getGoogleOAuthUrl();
      window.location.href = url;
    } catch (err) {
      if (err instanceof ApiError) {
        toast.error("Google sign-in is not configured on this server.");
      }
    }
  }, []);

  return {
    user,
    isAuthenticated,
    isLoading,
    isAdmin,
    isSuperuser,
    login,
    register,
    logout,
    changePassword,
    refreshProfile,
    loginWithGoogle,
  };
}
